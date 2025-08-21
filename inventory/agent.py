import os, re, json
from typing import Dict, Any
from dotenv import load_dotenv
load_dotenv()

class AgentParseError(Exception):
    pass

def _rule_based_parse(text: str) -> Dict[str, Any]:
    t = text.lower().strip()
    # Try to detect action
    if t.startswith("add") or " add " in t:
        # add 20 bananas with sku B300 price 90
        q = _find_int(t) or 1
        sku = _find_after(t, "sku") or _find_after(t, "code")
        price = _find_float_after(t, "price") or 0.0
        name = _find_name(t, exclude=["add","with","sku","price","update","delete","subtract"]) or (sku or "item")
        if not sku:
            raise AgentParseError("SKU not found; try '... with sku ABC123'")
        return {"type":"add","sku":sku.upper(),"name":name.title(),"quantity":q,"price":price}
    if t.startswith("subtract") or t.startswith("minus") or " subtract " in t or " remove " in t:
        q = _find_int(t) or 1
        sku = _find_after(t, "sku") or _find_after(t, "code")
        if not sku:
            raise AgentParseError("SKU not found for subtract.")
        return {"type":"subtract","sku":sku.upper(),"quantity":q}
    if t.startswith("update") or " update " in t or " change " in t:
        sku = _find_after(t, "sku") or _find_after(t, "code")
        if not sku:
            raise AgentParseError("SKU not found for update.")
        data = {"type":"update","sku":sku.upper()}
        q = _find_int_after(t, "qty") or _find_int_after(t, "quantity")
        if q is not None:
            data["quantity"] = q
        p = _find_float_after(t, "price")
        if p is not None:
            data["price"] = p
        nm = _find_after(t, "name")
        if nm:
            data["name"] = nm.title()
        if len(data.keys())==2:
            raise AgentParseError("Nothing to update (provide name/quantity/price)")
        return data
    if t.startswith("delete") or " delete " in t or t.startswith("remove") or " remove sku" in t:
        sku = _find_after(t, "sku") or _find_after(t, "code")
        if not sku:
            raise AgentParseError("SKU not found for delete.")
        return {"type":"delete","sku":sku.upper()}
    raise AgentParseError("Action not recognized. Try: add / subtract / update / delete.")

def _find_after(t: str, key: str):
    m = re.search(rf"{key}\s+([a-z0-9-_]+)", t)
    return m.group(1) if m else None

def _find_int(t: str):
    m = re.search(r"\b(\d+)\b", t)
    return int(m.group(1)) if m else None

def _find_int_after(t: str, key: str):
    m = re.search(rf"{key}[^0-9]*(\d+)", t)
    return int(m.group(1)) if m else None

def _find_float_after(t: str, key: str):
    m = re.search(rf"{key}[^0-9]*([0-9]+(?:\.[0-9]+)?)", t)
    return float(m.group(1)) if m else None

def _find_name(t: str, exclude=None):
    exclude = set(exclude or [])
    words = [w for w in re.findall(r"[a-z]+", t) if w not in exclude]
    # crude: take the longest word as name
    return max(words, key=len) if words else None

class Agent:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self._client = None
        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._client = genai.GenerativeModel("gemini-1.5-flash")
            except Exception:
                self._client = None

    def parse(self, text: str) -> Dict[str, Any]:
        """Return an action dict with keys:
        - type: add|subtract|update|delete
        - sku, name, quantity, price (depending on type)
        """
        # If Gemini available, try it first
        if self._client:
            try:
                prompt = f"""You are a strict JSON command parser for an inventory app.
                Allowed actions:
                  - add: requires sku (string), name (string), quantity (int), price (float)
                  - subtract: requires sku (string), quantity (int)
                  - update: requires sku (string) and any of name (string), quantity (int), price (float)
                  - delete: requires sku (string)
                Input: {text}
                Respond with ONLY minified JSON dictionary with a 'type' field and needed fields. No extra text.
                """
                res = self._client.generate_content(prompt)
                raw = res.text.strip()
                # Clean code fences if present
                raw = raw.strip('`')
                data = json.loads(raw)
                # Basic validation
                if data.get("type") not in {"add","subtract","update","delete"}:
                    raise AgentParseError("Invalid type from model")
                return data
            except Exception:
                # fallback
                pass
        # Rule-based fallback
        return _rule_based_parse(text)
