# from fastapi import FastAPI, Request, Depends, Form, HTTPException
# from fastapi.responses import HTMLResponse, RedirectResponse
# from fastapi.staticfiles import StaticFiles
# from fastapi.templating import Jinja2Templates
# from sqlalchemy.orm import Session
# from slowapi import Limiter, _rate_limit_exceeded_handler
# from slowapi.util import get_remote_address
# from slowapi.errors import RateLimitExceeded
# import hashlib, httpx, pandas as pd, os, uuid
# from datetime import datetime
# from contextlib import asynccontextmanager

# from database import engine, get_db , Base
# from models import User, Formulaire, Reponse
# from schemas import UserCreate, UserRead, UserUpdate
# from service_stats import generer_stats_completes

# from fastapi_users import FastAPIUsers
# from fastapi_users.authentication import CookieTransport, AuthenticationBackend
# from fastapi_users.authentication.strategy.db import DatabaseStrategy
# from fastapi_users.db import SQLAlchemyUserDatabase

# SECRET = os.getenv("SECRET")
# HCAPTCHA_SECRET = os.getenv("HCAPTCHA_SECRET")
# HCAPTCHA_SITEKEY = os.getenv("HCAPTCHA_SITEKEY")
# RATE_LIMIT = os.getenv("RATE_LIMIT", "3/1day")


# from auth import (
#     fastapi_users,
#     auth_backend,
#     current_user,
#     current_user_optional,
# )

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     Base.metadata.create_all(bind=engine)
#     yield

# limiter = Limiter(key_func=get_remote_address)
# app = FastAPI(lifespan=lifespan)
# app.state.limiter = limiter
# app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
# app.mount("/static", StaticFiles(directory="static"), name="static")
# templates = Jinja2Templates(directory="templates")

# async def get_user_db(session: Session = Depends(get_db )):
#     yield SQLAlchemyUserDatabase(session, User)

# cookie_transport = CookieTransport(cookie_max_age=3600)
# def get_database_strategy(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
#     return DatabaseStrategy(user_db, lifetime_seconds=3600)

# auth_backend = AuthenticationBackend(name="cookie", transport=cookie_transport, get_strategy=get_database_strategy)
# #fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_db, [auth_backend])
# #current_user = fastapi_users.current_user(active=True)

# app.include_router(fastapi_users.get_auth_router(auth_backend), prefix="/auth", tags=["auth"])
# app.include_router(fastapi_users.get_register_router(UserRead, UserCreate), prefix="/auth", tags=["auth"])

# def hash_ip(ip: str): return hashlib.sha256(ip.encode()).hexdigest()

# @app.get("/", response_class=HTMLResponse)
# def home(request: Request):
#     return templates.TemplateResponse("base.html", {"request": request})

# @app.get("/dashboard", response_class=HTMLResponse)
# def dashboard(request: Request, db: Session = Depends(get_db ), user: User = Depends(current_user)):
#     forms = db.query(Formulaire).filter(Formulaire.owner_id == user.id).order_by(Formulaire.created_at.desc()).all()
#     return templates.TemplateResponse("dashboard.html", {"request": request, "forms": forms})

# @app.get("/new", response_class=HTMLResponse)
# def page_builder(request: Request, user: User = Depends(current_user)):
#     return templates.TemplateResponse("builder.html", {"request": request})

# @app.post("/new")
# async def creer_formulaire(
#     request: Request,
#     db: Session = Depends(get_db ),
#     user: User = Depends(current_user),
#     titre: str = Form(...),
#     expires_at: str = Form(None),
#     structure: str = Form(...)
# ):
#     import json
#     date_fin = datetime.fromisoformat(expires_at) if expires_at else None
#     form = Formulaire(
#         titre=titre,
#         structure=json.loads(structure),
#         owner_id=user.id,
#         expires_at=date_fin
#     )
#     db.add(form)
#     db.commit()
#     return RedirectResponse(url="/dashboard", status_code=303)

# @app.get("/f/{form_id}", response_class=HTMLResponse)
# def afficher_formulaire(request: Request, form_id: uuid.UUID, db: Session = Depends(get_db )):
#     form = db.query(Formulaire).filter(Formulaire.id == form_id).first()
#     if not form: raise HTTPException(404, "Formulaire introuvable")
#     if not form.is_active or (form.expires_at and form.expires_at < datetime.utcnow()):
#         return templates.TemplateResponse("form_ferme.html", {"request": request, "form": form})
#     return templates.TemplateResponse("form_public.html", {"request": request, "form": form, "sitekey": HCAPTCHA_SITEKEY})

# @app.post("/f/{form_id}/submit")
# @limiter.limit(RATE_LIMIT)
# async def soumettre_reponse(request: Request, form_id: uuid.UUID, db: Session = Depends(get_db ), h_captcha_response: str = Form(alias="h-captcha-response")):
#     form = db.query(Formulaire).filter(Formulaire.id == form_id).first()
#     if not form or not form.is_active or (form.expires_at and form.expires_at < datetime.utcnow()):
#         raise HTTPException(403, "Sondage terminé")

#     async with httpx.AsyncClient() as client:
#         res = await client.post("https://hcaptcha.com/siteverify", data={"secret": HCAPTCHA_SECRET, "response": h_captcha_response})
#         if not res.json().get("success"): raise HTTPException(400, "Captcha invalide")

#     form_data = await request.form()
#     data_dict = {k: v for k, v in form_data.items() if k!= 'h-captcha-response'}
#     db.add(Reponse(form_id=form_id, data=data_dict, ip_hash=hash_ip(get_remote_address(request))))
#     db.commit()
#     return RedirectResponse(url="/merci", status_code=303)

# @app.get("/merci", response_class=HTMLResponse)
# def page_merci(request: Request):
#     return templates.TemplateResponse("merci.html", {"request": request})

# @app.get("/f/{form_id}/stats", response_class=HTMLResponse)
# def voir_stats(request: Request, form_id: uuid.UUID, db: Session = Depends(get_db ), user: User = Depends(current_user)):
#     form = db.query(Formulaire).filter(Formulaire.id == form_id, Formulaire.owner_id == user.id).first()
#     if not form: raise HTTPException(404)

#     reponses = db.query(Reponse).filter(Reponse.form_id == form_id).all()
#     if not reponses: return templates.TemplateResponse("stats.html", {"request": request, "form": form, "df_empty": True})

#     df = pd.DataFrame([r.data for r in reponses])
#     stats = generer_stats_completes(df, form_id)
#     return templates.TemplateResponse("stats.html", {"request": request, "form": form, "stats": stats, "nb_reponses": len(df)})

# @app.post("/f/{form_id}/cloturer")
# def cloturer_formulaire(form_id: uuid.UUID, db: Session = Depends(get_db ), user: User = Depends(current_user)):
#     form = db.query(Formulaire).filter(Formulaire.id == form_id, Formulaire.owner_id == user.id).first()
#     if not form: raise HTTPException(404)
#     form.is_active = False
#     db.commit()
#     return RedirectResponse(url="/dashboard", status_code=303)

# @app.post("/f/{form_id}/rouvrir")
# def rouvrir_formulaire(form_id: uuid.UUID, db: Session = Depends(get_db ), user: User = Depends(current_user)):
#     form = db.query(Formulaire).filter(Formulaire.id == form_id, Formulaire.owner_id == user.id).first()
#     if not form: raise HTTPException(404)
#     form.is_active = True
#     db.commit()
#     return RedirectResponse(url="/dashboard", status_code=303)

# @app.post("/f/{form_id}/vider")
# def vider_reponses(form_id: uuid.UUID, db: Session = Depends(get_db ), user: User = Depends(current_user)):
#     form = db.query(Formulaire).filter(Formulaire.id == form_id, Formulaire.owner_id == user.id).first()
#     if not form: raise HTTPException(404)
#     db.query(Reponse).filter(Reponse.form_id == form_id).delete()
#     db.commit()
#     return RedirectResponse(url="/dashboard", status_code=303)


# @app.get("/auth/login", response_class=HTMLResponse)
# def login_page(request: Request):
#     return templates.TemplateResponse("login.html", {"request": request})

# @app.get("/auth/register", response_class=HTMLResponse)
# def register_page(request: Request):
#     return templates.TemplateResponse("register.html", {"request": request})



import hashlib, httpx, pandas as pd, os, uuid, json
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from database import engine, get_async_session, Base
from models import User, Formulaire, Reponse
from schemas import UserCreate, UserRead, UserUpdate
from service_stats import generer_stats_completes
from auth import fastapi_users, auth_backend, current_user, current_user_optional, get_user_manager

HCAPTCHA_SECRET = os.getenv("HCAPTCHA_SECRET")
HCAPTCHA_SITEKEY = os.getenv("HCAPTCHA_SITEKEY")
RATE_LIMIT = os.getenv("RATE_LIMIT", "3/1day")

# --- Lifespan ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

# --- App ---
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- Routers fastapi-users ---
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/cookie",
    tags=["auth"],
)
# app.include_router(
#     fastapi_users.get_register_router(UserRead, UserCreate),
#     prefix="/auth",
#     tags=["auth"],
# )

# --- Utilitaire ---
def hash_ip(ip: str):
    return hashlib.sha256(ip.encode()).hexdigest()

# --- Pages publiques ---
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return RedirectResponse(url="/auth/login", status_code=302)
    #templates.TemplateResponse(name = "login.html", request= request)

@app.get("/auth/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(name="login.html", request= request)

@app.get("/auth/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse(name = "register.html", request = request)


@app.post("/auth/register", response_class=HTMLResponse)
async def register_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    user_manager=Depends(get_user_manager)
):
    try:
        user_create = UserCreate(email=email, password=password)
        await user_manager.create(user_create, safe=True, request=request)
        # Inscription OK → redirection vers login
        return RedirectResponse(url="/auth/login?registered=1", status_code=303)
    except UserAlreadyExists:
        return templates.TemplateResponse(name = "register.html",
            request = request, context={
            "error": "Un compte existe déjà avec cet email."
        })
    except Exception as e:
        return templates.TemplateResponse(name = "register.html", 
            request= request,context = {
            "error": f"Erreur : {str(e)}"
        })



@app.get("/merci", response_class=HTMLResponse)
def page_merci(request: Request):
    return templates.TemplateResponse(name = "merci.html", request= request)

# --- Pages protégées ---
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user_optional)
):
    if user is None:
        return RedirectResponse(url="/auth/login", status_code=302)
    from sqlalchemy import select
    result = await db.execute(
        select(Formulaire)
        .where(Formulaire.owner_id == user.id)
        .order_by(Formulaire.created_at.desc())
    )
    forms = result.scalars().all()
    return templates.TemplateResponse(name = "dashboard.html", 
        request = request,context = {
        "forms": forms,
        "user": user
    })

@app.get("/new", response_class=HTMLResponse)
def page_builder(
    request: Request,
    user: User = Depends(current_user_optional)
):
    if user is None:
        return RedirectResponse(url="/auth/login", status_code=302)
    return templates.TemplateResponse(name = "builder.html", request = request, context = {"user": user})

@app.post("/new")
async def creer_formulaire(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user_optional),
    titre: str = Form(...),
    expires_at: str = Form(None),
    structure: str = Form(...)
):
    if user is None:
        return RedirectResponse(url="/auth/login", status_code=302)
    date_fin = datetime.fromisoformat(expires_at) if expires_at else None
    form = Formulaire(
        titre=titre,
        structure=json.loads(structure),
        owner_id=user.id,
        expires_at=date_fin
    )
    db.add(form)
    await db.commit()
    return RedirectResponse(url="/dashboard", status_code=303)

# --- Formulaires publics ---
@app.get("/f/{form_id}", response_class=HTMLResponse)
async def afficher_formulaire(
    request: Request,
    form_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session)
):
    from sqlalchemy import select
    result = await db.execute(select(Formulaire).where(Formulaire.id == form_id))
    form = result.scalar_one_or_none()
    if not form:
        raise HTTPException(404, "Formulaire introuvable")
    if not form.is_active or (form.expires_at and form.expires_at < datetime.utcnow()):
        return templates.TemplateResponse(name = "form_ferme.html", request = request,context= { "form": form})
    return templates.TemplateResponse(name = "form_public.html", 
        request = request, context = {
        "form": form,
        "sitekey": HCAPTCHA_SITEKEY
    })

@app.post("/f/{form_id}/submit")
@limiter.limit(RATE_LIMIT)
async def soumettre_reponse(
    request: Request,
    form_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
    #h_captcha_response: str = Form(alias="h-captcha-response")
):
    from sqlalchemy import select
    result = await db.execute(select(Formulaire).where(Formulaire.id == form_id))
    form = result.scalar_one_or_none()
    if not form or not form.is_active or (form.expires_at and form.expires_at < datetime.utcnow()):
        raise HTTPException(403, "Sondage terminé")

    """async with httpx.AsyncClient() as client:
        res = await client.post(
            "https://hcaptcha.com/siteverify",
            data={"secret": HCAPTCHA_SECRET, "response": h_captcha_response}
        )
        result = res.json()
        print("HCAPTCHA RESPONSE:", result)      # ← ajoute ça
        print("TOKEN RECU:", h_captcha_response) # ← et ça
        if not res.json().get("success"):
            raise HTTPException(400, "Captcha invalide")

    print("Etape de Captcha Réussi-")"""
    form_data = await request.form()
    data_dict = {k: v for k, v in form_data.items() if k != "h-captcha-response"}
    db.add(Reponse(
        form_id=form_id,
        data=data_dict,
        ip_hash=hash_ip(get_remote_address(request))
    ))
    await db.commit()
    return RedirectResponse(url="/merci", status_code=303)

# --- Stats ---
@app.get("/f/{form_id}/stats", response_class=HTMLResponse)
async def voir_stats(
    request: Request,
    form_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user_optional)
):
    if user is None:
        return RedirectResponse(url="/auth/login", status_code=302)
    from sqlalchemy import select
    result = await db.execute(
        select(Formulaire).where(Formulaire.id == form_id, Formulaire.owner_id == user.id)
    )
    form = result.scalar_one_or_none()
    if not form:
        raise HTTPException(404)
    result2 = await db.execute(select(Reponse).where(Reponse.form_id == form_id))
    reponses = result2.scalars().all()
    print(reponses[0].data)  # ← ajoute ça pour voir les réponses dans les logs
    if not reponses:
        return templates.TemplateResponse(name = "stats.html", 
            request = request,context={ "form": form, "df_empty": True
        })
    structure = form.structure  # ton JSONB, ex: [{"name": "q1", "label": "Quel est ton âge ?", ...}]
    label_map = {champ["nom"]: champ.get("label", champ["nom"]) for champ in structure}

    df = pd.DataFrame([r.data for r in reponses])
    df = df.rename(columns=label_map)
    stats = generer_stats_completes(df, form_id)
    return templates.TemplateResponse(name = "stats.html", 
        request = request, context={ "form": form, "stats": stats, "nb_reponses": len(df)
    })

# --- Actions formulaire ---
@app.post("/f/{form_id}/cloturer")
async def cloturer_formulaire(
    form_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user_optional)
):
    if user is None:
        return RedirectResponse(url="/auth/login", status_code=302)
    from sqlalchemy import select
    result = await db.execute(
        select(Formulaire).where(Formulaire.id == form_id, Formulaire.owner_id == user.id)
    )
    form = result.scalar_one_or_none()
    if not form:
        raise HTTPException(404)
    form.is_active = False
    await db.commit()
    return RedirectResponse(url="/dashboard", status_code=303)

@app.post("/f/{form_id}/rouvrir")
async def rouvrir_formulaire(
    form_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user_optional)
):
    if user is None:
        return RedirectResponse(url="/auth/login", status_code=302)
    from sqlalchemy import select
    result = await db.execute(
        select(Formulaire).where(Formulaire.id == form_id, Formulaire.owner_id == user.id)
    )
    form = result.scalar_one_or_none()
    if not form:
        raise HTTPException(404)
    form.is_active = True
    await db.commit()
    return RedirectResponse(url="/dashboard", status_code=303)

@app.post("/f/{form_id}/vider")
async def vider_reponses(
    form_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user_optional)
):
    if user is None:
        return RedirectResponse(url="/auth/login", status_code=302)
    from sqlalchemy import select, delete
    result = await db.execute(
        select(Formulaire).where(Formulaire.id == form_id, Formulaire.owner_id == user.id)
    )
    form = result.scalar_one_or_none()
    if not form:
        raise HTTPException(404)
    await db.execute(delete(Reponse).where(Reponse.form_id == form_id))
    await db.commit()
    return RedirectResponse(url="/dashboard", status_code=303)  
