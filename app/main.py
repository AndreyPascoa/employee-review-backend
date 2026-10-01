from fastapi import FastAPI
from app.routers.employees import router as employees_router
from app.routers.questions import router as questions_router
from app.routers.evaluations import router as evaluations_router
from app.routers.leaders import router as leaders_router

app = FastAPI(  
    title="Employee Review API",
    description="API de avaliação de funcionario",
    version="0.1.0"
)

@app.get("/health", tags=["Infraestrutura"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}

app.include_router(employees_router, prefix="/api")
app.include_router(questions_router, prefix="/api")
app.include_router(evaluations_router, prefix="/api")
app.include_router(leaders_router, prefix="/api")