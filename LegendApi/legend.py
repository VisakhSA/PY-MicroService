import os
import requests
from fastapi import FastAPI, Body, HTTPException, status
from fastapi.responses import Response, JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId
from typing import Optional, List
import motor.motor_asyncio

app = FastAPI()
mysportapi = os.getenv('mysportapi')
mymongo = os.getenv('mymongo')

client = motor.motor_asyncio.AsyncIOMotorClient(f'mongodb://{mymongo}:27017')
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


class LegendModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    legendName: str = Field(...)
    sportName: str = Field(...)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "legendName": "Sachin",
                "sportName": "Cricket"
            }
        }


class UpdateLegendModel(BaseModel):
    curr_name: Optional[str] = Field(...)
    update_name: Optional[str] = Field(...)


@app.post("/legend", response_description="Add new legend")
async def create_legend(legend: LegendModel = Body(...)):
    legend = jsonable_encoder(legend)
    sports = requests.get(url=f'http://{mysportapi}:80/sports')
    sports = sports.json()
    sport_name = []
    for i in sports:
        sport_name.append(i["sportName"])
    if legend["sportName"] in sport_name:
        new_legend = await db["legend"].insert_one(legend)
        created_legend = await db["legend"].find_one({"_id": new_legend.inserted_id})
        return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_legend)
    return {"msg": "Sport not present in list"}


@app.get("/legends", response_description="List all legends")
async def list_legends():
    legends = await db["legend"].find().to_list(1000)
    return legends


@app.get("/sports", response_description="List all the sports")
async def list_sports():
    sports = requests.get(url=f'http://{mysportapi}:80/sports')
    sports = sports.json()
    sport_name = []
    for i in sports:
        sport_name.append(i["sportName"])
    return sport_name


@app.put("/legend/multiupdate", response_description="Updates the sportname of a legend if sportname is changed on the sport microservice")
async def update_legend(updationdata: UpdateLegendModel = Body(...)):
    updationdata = jsonable_encoder(updationdata)
    update_result = await db["legend"].update_many({"sportName": updationdata["curr_name"]}, {"$set": {"sportName": updationdata["update_name"]}})
    if update_result.modified_count > 0:
        return {"message": "Successfully Updated"}
    return {"message": f'No Legend is associated with the sport name {updationdata["curr_name"]}'}


@app.delete("/legend/multidelete", response_description="Deletes a legend record associated with a sportname when sportname is deleted at the sport microservice")
async def delete_legend(deleteName: str):
    delete_result = await db["legend"].delete_many({"sportName": deleteName})

    if delete_result.deleted_count > 0:
        return Response(status_code=status.HTTP_204_NO_CONTENT), {"message": "Successfully Deleted"}

    raise HTTPException(
        status_code=404, detail=f"There is no legends associated with {deleteName} in db")


@app.delete("/legend/{id}", response_description="Delete a legend")
async def delete_legend(id: str):
    delete_result = await db["legend"].delete_one({"_id": id})

    if delete_result.deleted_count == 1:
        return {"message": "Successfully Deleted"}

    raise HTTPException(status_code=404, detail=f"legend_id {id} not found")
