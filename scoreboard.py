from fastapi import FastAPI, Header, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import pandas as pd
import json
import secrets
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = FastAPI()



# Use environment variables
allow_origins = os.getenv('ALLOW_ORIGINS', '*').split(',')
expected_api_key = os.getenv('API_KEY', 'secret')

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,  # Use environment variable
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the data from the JSON file into a DataFrame
df = pd.read_json('scoreboard.json')



async def get_api_key(x_api_key: str = Header(...)):
    global expected_api_key
    if x_api_key != expected_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )

# get scoreboard for specific level
@app.get("/scoreboard/{level}")
def scoreboard_list(level: int):
    # return sorted by time
    return df[df['level'] == level].sort_values(by='time').to_dict(orient='records')
    


@app.post("/scoreboard/submit")
async def submit_json(data: dict, api_key: str = Depends(get_api_key)):
    if 'level' not in data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Level not found in request data"
        )
    if 'playerName' not in data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Name not found in request data"
        )
    if 'time' not in data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Timestamp not found in request data"
        )
    if 'level' in data and 'playerName' in data and 'time' in data:
        # Check if there is an existing entry for the given level and playerName
        existing_entry_index = df[(df['level'] == data['level']) & (df['playerName'] == data['playerName'])].index

        if not existing_entry_index.empty:
            # Get the existing time for comparison
            existing_time = df.at[existing_entry_index[0], 'time']
            # Update the time for the existing entry only if the new time is better
            if data['time'] < existing_time:
                df.at[existing_entry_index[0], 'time'] = data['time']
            else :
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="New time is not better than existing time"
                )
        else:
            # Add a new entry
            df.loc[len(df.index)] = [data['level'], data['playerName'], data['time']]

        # Save the updated DataFrame to JSON
        df.to_json('scoreboard.json', orient='records')
        return {'status': 'success'}
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid request data"
        )
    
    