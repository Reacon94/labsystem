from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from bson import ObjectId
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Erlaubt alle Ursprünge (für Entwicklung)
    allow_credentials=True,
    allow_methods=["*"],  # Erlaubt alle Methoden (GET, POST, etc.)
    allow_headers=["*"],  # Erlaubt alle Header
)

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client.lab_db
samples_collection = db.samples
tests_collection = db.tests

# Helper to convert MongoDB ObjectId
def convert_objectid(obj):
    obj["_id"] = str(obj["_id"])
    return obj

# Pydantic models for Sample and Test
class Sample(BaseModel):
    _id: Optional[str]  # Optional, wird beim Erstellen nicht benötigt
    sample_id: str = Field(..., description="Eindeutige ID für das Sample")
    patient_name: str = Field(..., description="Name des Patienten")
    lab_info: Dict[str, str] = Field(..., description="Informationen zu den Labortests")
    description: Optional[str] = Field(None, description="Beschreibung des Samples")

class Test(BaseModel):
    sample_id: str = Field(..., description="ID of the sample associated with the test")
    test_type: str = Field(..., description="Type of the test")
    result: Optional[str] = Field(None, description="Result of the test")
    units: Optional[str] = Field(None, description="Units of the test result")
    

# Sample creation endpoint
@app.post("/samples/", response_model=Sample)
async def create_sample(sample: Sample):
    sample_dict = sample.dict()  # Konvertiere Pydantic-Modell in ein Dictionary
    # Generiere eine neue ObjectId und speichere sie in sample_id
    sample_dict["sample_id"] = str(ObjectId())  # Hier wird die ObjectId als sample_id gespeichert
    result = samples_collection.insert_one(sample_dict)
    sample_dict["_id"] = str(result.inserted_id)  # Füge die ObjectId hinzu
    return sample_dict


# Sample retrieval endpoint
@app.get("/samples/", response_model=List[Sample])
async def list_samples():
    samples = list(samples_collection.find())
    return [convert_objectid(sample) for sample in samples]

@app.get("/samples/{sample_id}", response_model=Sample)
async def get_sample(sample_id: str):
    sample = samples_collection.find_one({"sample_id": sample_id})  # Suche nach sample_id
    if sample:
        return convert_objectid(sample)  # Verwende die Konvertierungsfunktion
    else:
        raise HTTPException(status_code=404, detail="Sample not found")


# Sample update endpoint
@app.put("/samples/{sample_id}", response_model=Sample)
async def update_sample(sample_id: str, sample: Sample):
    result = samples_collection.find_one_and_update(
        {"sample_id": sample_id},
        {"$set": sample.dict(exclude_unset=True)},
        return_document=True
    )
    if result:
        result["_id"] = str(result["_id"])  # Convert ObjectId to string for JSON
        return result
    else:
        raise HTTPException(status_code=404, detail="Sample not found")

# Sample deletion endpoint
@app.delete("/samples/{sample_id}", response_model=dict)
async def delete_sample(sample_id: str):
    result = samples_collection.delete_one({"sample_id": sample_id})
    if result.deleted_count == 1:
        return {"message": "Sample deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Sample not found")

# Test creation endpoint
@app.post("/tests/", response_model=Test)
async def create_test(test: Test):
    test_dict = test.dict(exclude_unset=True)  # Convert Pydantic model to dict
    result = tests_collection.insert_one(test_dict)
    test_dict["_id"] = str(result.inserted_id)  # Add the new ObjectId to the test dict
    return test_dict

@app.get("/tests/", response_model=List[Test])
async def list_tests():
    tests = list(tests_collection.find())
    return [convert_objectid(test) for test in tests]

# Test creation endpoint for a specific sample
@app.post("/samples/{sample_id}/tests", response_model=Test)
async def create_test_for_sample(sample_id: str, test: Test):
    test_dict = test.dict(exclude_unset=True)
    test_dict["sample_id"] = sample_id
    result = tests_collection.insert_one(test_dict)
    test_dict["_id"] = str(result.inserted_id)
    return test_dict

# Test list endpoint for a specific sample
@app.get("/samples/{sample_id}/tests", response_model=List[Test])
async def list_tests_for_sample(sample_id: str):
    tests = list(tests_collection.find({"sample_id": sample_id}))
    return [convert_objectid(test) for test in tests]

# Test update endpoint for a specific sample
@app.put("/samples/{sample_id}/tests/{test_type}", response_model=Test)
async def update_test(sample_id: str, test_type: str, test: Test):
    result = tests_collection.find_one_and_update(
        {"sample_id": sample_id, "test_type": test_type},
        {"$set": test.dict(exclude_unset=True)},
        return_document=True
    )
    if result:
        result["_id"] = str(result["_id"])  # Convert ObjectId to string for JSON
        return result
    else:
        raise HTTPException(status_code=404, detail="Test not found")

