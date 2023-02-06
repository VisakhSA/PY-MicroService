# Use the official MongoDB image from the Docker Hub
FROM mongo:latest

# Copy the script that creates the collection to the container
COPY createComponent.js /docker-entrypoint-initdb.d/

# Set the default command to run the MongoDB service.
CMD ["mongod"]
