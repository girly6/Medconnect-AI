from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import engine, get_db
from app import models, schemas, crud
from app.ai.graph import agent

class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MedConnect AI API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {
        "message": "Welcome to MedConnect AI Backend"
    }


@app.get("/health")
def health():
    return {
        "status": "Backend Running Successfully"
    }


@app.post("/interactions", response_model=schemas.InteractionResponse)
def create_interaction(
    interaction: schemas.InteractionCreate,
    db: Session = Depends(get_db)
):
    return crud.create_interaction(db, interaction)

    
@app.get("/interactions", response_model=list[schemas.InteractionResponse])
def get_interactions(db: Session = Depends(get_db)):
    return crud.get_interactions(db)

@app.get("/analytics")
def get_analytics(db: Session = Depends(get_db)):

    interactions = crud.get_interactions(db)

    total = len(interactions)

    high = len(
        [i for i in interactions if i.priority.lower() == "high"]
    )

    medium = len(
        [i for i in interactions if i.priority.lower() == "medium"]
    )

    low = len(
        [i for i in interactions if i.priority.lower() == "low"]
    )

    product_counts = {}

    for interaction in interactions:

        product = interaction.product

        if product not in product_counts:
            product_counts[product] = 0

        product_counts[product] += 1

    monthly_counts = {}

    for interaction in interactions:

        month = interaction.visit_date.strftime("%b")

        if month not in monthly_counts:
            monthly_counts[month] = 0

        monthly_counts[month] += 1

    return {

        "total": total,

        "high": high,

        "medium": medium,

        "low": low,

        "products": product_counts,

        "monthly": monthly_counts

    }

@app.delete("/interactions/{interaction_id}")
def delete_interaction(
    interaction_id: int,
    db: Session = Depends(get_db),
):

    interaction = crud.delete_interaction(
        db,
        interaction_id
    )

    if interaction is None:
        raise HTTPException(
            status_code=404,
            detail="Interaction not found"
        )

    return {
        "message": "Interaction Deleted Successfully"
    }


@app.post("/chat")
def chat(request: ChatRequest):

    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": request.message
                }
            ]
        }
    )

    messages = result["messages"]

    final_response = messages[-1].content

    return {
        "response": final_response
    }