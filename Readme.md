pip install -r requirements.txt
dev: 
    uvicorn main:app --reload
stable:
    uvicorn main:app

