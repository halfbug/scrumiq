from time import time
from pymongo import MongoClient
from core.config import config
from contextlib import asynccontextmanager
from fastapi import FastAPI, __version__
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from api.routes import api_router_v1
from core.initialize import set_environment_variables
from core.mongoengine_connect import init_mongoengine

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.mongodb_client = MongoClient(config.MONGO_URI)
    app.database = app.mongodb_client[config.MONGO_DB]
    print("Connected to the MongoDB database!")
    yield
    app.mongodb_client.close()

app = FastAPI(lifespan=lifespan)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

html = f"""
<!DOCTYPE html>
<html>
    <head>
        <title>FastAPI on Vercel</title>
        <link rel="icon" href="/static/favicon.ico" type="image/x-icon" />
    </head>
    <body>
        <div class="bg-gray-200 p-4 rounded-lg shadow-lg">
            <h1>Hello from FastAPI@{__version__}</h1>
            <ul>
                <li><a href="/docs">/docs</a></li>
                <li><a href="/redoc">/redoc</a></li>
            </ul>
            <p>Powered by <a href="https://vercel.com" target="_blank">Vercel</a></p>
        </div>
    </body>
</html>
"""

@app.get("/")
async def root():
    return HTMLResponse(html)

@app.get('/ping')
async def hello():
    return {'res': 'pong', 'version': __version__, "time": time()}
# Add this middleware setup at the top-level (before router definition)
def add_user_id_middleware(app: FastAPI):
    @app.middleware("http")
    async def user_id_middleware(request, call_next):
        user_id = None
        # Try to get user_id from header first
        if "user-id" in request.headers:
            user_id = request.headers["user-id"]
        else:
            # Try to get user_id from JSON body if present
            try:
                body = await request.json()
                user_id = body.get("user_id")
            except Exception:
                pass
        request.state.user_id = user_id
        response = await call_next(request)
        set_environment_variables()
        return response

# Example usage: in your main app file, after creating FastAPI app:
# from api.v1.stream import add_user_id_middleware
add_user_id_middleware(app)
# app.include_router(router)
init_mongoengine()

@app.get("/")
def read_root():
    return {"Status": "Success", "Message": "Api is working on " + config.API_V1_ROUTE}

# Add Routers updated
print("Print config API_V1_ROUTE", config.API_V1_ROUTE)
app.include_router(api_router_v1, prefix=config.API_V1_ROUTE)