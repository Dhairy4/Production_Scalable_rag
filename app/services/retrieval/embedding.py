import time
import logfire
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings



BATCH_SIZE = 50 
GEMINI_DIM = 3072
FALLBACK_DIM = 768 # all-mpent-base-v2


active_model = None
model_type = str | None = None

def probe_gemini():
    """
    try one embed call to verify gemini is reachable
    """

    try:
        model = ChatGoogleGenerativeAI(
            model = "models/gemini-embedding-2-preview",
            google_api_key = settings.GEMINI_API_KEY
        )

        model.embed_query("probe")
        logfire.info("Gemini is ready (gemini embedding-2-preview 3072 dim)") 
        return model

    except Exception as e:
        logfire.error(f"Gemini probe failed: {e}")
        return None

def load_feedback():
    from sentence_transformers import SentenceTransformer
    logfire.info("Loading fallback model (all-mpnet-base-v2 768 dim)")
    return SentenceTransformer("all-mpnet-base-v2")

def init():
    global active_model, model_type
    if active_model is not None:
        return 

    gemini = probe_gemini()
    if gemini:
        active_model = gemini
        model_type = "gemini"

    else:
        active_model = load_feedback()
        model_type = "fallback"
    return 

def get_embedding_dim():
    """
    return the dimension of the active model. call after _init()
    """
    init()
    return GEMINI_DIM if model_type == "gemini" else FALLBACK_DIM

def embed_batch(batch: list[str]) -> list[list[float]]:

    if model_type == "gemini":
        for attempt in range(4):
            try: 
                return active_model.embed_documents(batch)
            except Exception as e:
                err = str(e).lower()
                is_rate_limit = any(x in err for x in ["rate limit", "quota exceeded", "429"])
                if is_rate_limit and attempt < 3:
                    wait = 2** attempt
                    logfire.warning(f"Gemini rate limit hit, retrying in {2**attempt} seconds...")
                    time.sleep(wait)
                else:
                    logfire.error(f"gemini embedding failed {e}") 
                    raise

        raise RuntimeError("Gemini rate limit presists after 4 attempts")             

    else:
        return active_model.encode(batch, convert_to_numpy=True).tolist()


def embed_query(query: str) -> list[float]:
    init()
    if model_type == "gemini":
        return active_model.embed_query(query)  
    return active_model.encode(query, convert_to_numpy=True)[0].tolist()

def embed_text(texts: list[str]) -> list[list[float]]:
    init()
    all_embeddings: list[list[float]] =  []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i: i + BATCH_SIZE]
        with logfire.span("embed batch", model= model_type, start=i, end=i+len(batch)):
        
            all_embeddings.extend(embed_batch(batch))
    return all_embeddings