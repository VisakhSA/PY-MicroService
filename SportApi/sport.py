import os
import json
import requests
from fastapi import FastAPI, Body, HTTPException, status
from fastapi.responses import Response, JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId
from typing import Optional, List
import motor.motor_asyncio

app = FastAPI()
client = motor.motor_asyncio.AsyncIOMotorClient('mongodb://mymongo:27017')
db = client.legend_sport


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class SportModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    sportName: str = Field(...)
    nationalGameOfCountry: str = Field(...)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "sportName": "Cricket",
                "nationalGameOfCountry": "AUS"
            }
        }


class UpdateSportModel(BaseModel):
    sportName: Optional[str] = Field(...)
    nationalGameOfCountry: Optional[str] = Field(...)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "sportName": "Cricket",
                "nationalGameOfCountry": "AUS"
            }
        }


@app.post("/sport", response_description="Add new sport")
async def create_sport(sport: SportModel = Body(...)):
    sport = jsonable_encoder(sport)
    new_sport = await db["sport"].insert_one(sport)
    created_sport = await db["sport"].find_one({"_id": new_sport.inserted_id})
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_sport)


@app.get("/sports", response_description="List all sports")
async def list_sports():
    sports = await db["sport"].find().to_list(1000)
    return sports


@app.put("/sport/{id}", response_description="Update a sport")
async def update_sport(id: str, sport: UpdateSportModel = Body(...)):
    sport = {k: v for k, v in sport.dict().items() if v is not None}

    if len(sport) >= 1:
        if "sportName" in sport:
            curr_name = await db["sport"].find_one({"_id": id})
            if curr_name is not None:
                data = {
                    "curr_name": curr_name["sportName"], "update_name": sport["sportName"]}
                r = requests.put(url=f'http://mylegendapi:81/legend/multiupdate', data=json.dumps(data), headers={
                                 'Content-Type': 'application/json', 'accept': 'application/json'})
                r = r.json()
                if "message" not in r:
                    return "Legend microservice is not working"
            else:
                raise HTTPException(
                    status_code=404, detail=f"sport_id {id} not found")
        update_result = await db["sport"].update_one({"_id": id}, {"$set": sport})

        if update_result.modified_count == 1:
            updated_sport = await db["sport"].find_one({"_id": id})
            if updated_sport is not None:
                return {"message": f'sportName of id {id} updated to {sport["sportName"]}'}
        else:
            return {"message": "No new updates on the body"}


@app.delete("/sport/{id}", response_description="Delete a sport")
async def delete_sport(id: str):
    curr_name = await db["sport"].find_one({"_id": id})

    if curr_name is not None:
        r = requests.delete(
            url=f'http://mylegendapi:81/legend/multidelete?deleteName={curr_name["sportName"]}')
        delete_result = await db["sport"].delete_one({"_id": id})

        if delete_result.deleted_count == 1:
            return {"message": "Successfully Deleted"}

    raise HTTPException(status_code=404, detail=f"sport_id {id} not found")
