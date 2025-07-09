from flask import Flask, request, render_template
import requests
from bs4 import BeautifulSoup
import socket
import whois

app = Flask(__name__)

def analyze_domain(domain):
    url = f"http://{domain}"
    result = {
        "URL": domain,
        "Status": "❓ Need Manual Check",
        "Reasoning": []
    }

    try:
        # WHOIS check
        try:
            w = whois.whois(domain)
            if not w.domain_name:
                result["Status"] = "❓ Need Manual Check"
                result["Reasoning"].append("Domain not registered (WHOIS check).")
                return result
        except Exception:
            result["Status"] = "❓ Need Manual Check"
            result["Reasoning"].append("WHOIS check failed.")
            return result

        # DNS resolution
        try:
            socket.gethostbyname(domain)
        except socket.gaierror:
            result["Status"] = "❓ Need Manual Check"
            result["Reasoning"].append("DNS resolution failed.")
            return result

        # Fetching the page
        res = requests.get(url, timeout=10, allow_redirects=True)
        html = res.text.lower()
        soup = BeautifulSoup(html, "html.parser")
        body_text = soup.get_text(separator=" ").lower()
        full_url = res.url.lower()

        # Landing / parked / sale page patterns
        landing_keywords = [
            "buy this domain", "domain for sale", "this domain is for sale",
            "available at auction", "expired domain", "make an offer",
            "register or transfer", "build your website", "coming soon",
            "website is for sale", "purchase this domain", "parked"
        ]
        landing_hosts = ["sedo.com", "dan.com", "dynadot.com", "afternic.com", "godaddy.com", "porkbun.com"]

        if any(kw in html for kw in landing_keywords) or \
           any(h in full_url for h in landing_hosts):
            result["Status"] = "📄 Landing Page"
            result["Reasoning"].append("Sale/parked/coming soon keywords or domain hosts matched.")
            return result

        # Live site detection logic
        indicators = [
            len(soup.find_all("nav")) > 0,
            len(soup.find_all("header")) > 0,
            len(soup.find_all("footer")) > 0,
            len(soup.find_all("a")) > 10,
            any(term in body_text for term in ["login", "signup", "blog", "product", "contact", "about us"])
        ]

        if any(indicators):
            result["Status"] = "✅ Live Site"
            result["Reasoning"].append("Detected navigation, footer/header, or relevant content.")
            return result

        # If content exists but no strong indicators
        if len(body_text.strip()) > 50:
            result["Status"] = "❓ Need Manual Check"
            result["Reasoning"].append("Content found but lacks strong structure to classify.")
        else:
            result["Status"] = "❓ Need Manual Check"
            result["Reasoning"].append("No significant content detected.")

    except Exception as e:
        result["Status"] = "❓ Need Manual Check"
        result["Reasoning"].append(f"Exception occurred: {str(e)}")

    return result


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    if request.method == "POST":
        domain = request.form["domain"].strip().replace("https://", "").replace("http://", "").rstrip("/")
        result = analyze_domain(domain)
    return render_template("index.html", result=result)


# if __name__ == "__main__":
#     app.run(debug=False, host='0.0.0.0', port=5001)
