from flask import Flask, request, render_template
import requests
from bs4 import BeautifulSoup
import socket

app = Flask(__name__)

def analyze_domain(domain):
    url = f"http://{domain}"
    result = {
        "URL": domain,
        "Status": "🟠 Unknown",
        "Confidence": 50,
        "Reasoning": [],
        "WhyNot100": []
    }

    try:
        try:
            socket.gethostbyname(domain)
        except socket.gaierror:
            result["Status"] = "❌ Unregistered or Invalid"
            result["Confidence"] = 100
            result["Reasoning"].append("• Domain did not resolve (DNS failure)")
            return result

        res = requests.get(url, timeout=8)
        html = res.text
        soup = BeautifulSoup(html, "html.parser")
        title = soup.title.string.lower() if soup.title else ""
        body_text = soup.get_text().lower()
        full_url = res.url.lower()

        if res.history:
            status_codes = [h.status_code for h in res.history]
            if any(code in [301, 302] for code in status_codes):
                result["Reasoning"].append(f"• Redirected ({status_codes[-1]}) to {res.url}")
                result["WhyNot100"].append("• Redirect may mask original content")

        sale_keywords = [
            "buy this domain", "domain for sale", "this domain is for sale",
            "available at auction", "expired domain", "make an offer",
            "register or transfer", "build your website", "dynadot", "sedo", "dan.com", "afternic"
        ]

        if any(kw in title for kw in sale_keywords) or \
           any(kw in body_text for kw in sale_keywords) or \
           any(salehost in full_url for salehost in ["sedo.com", "dan.com", "dynadot.com", "afternic.com"]):
            result["Status"] = "🔴 For Sale (Lander)"
            result["Confidence"] = 96
            result["Reasoning"].append("• Sale-related keywords or marketplace URL found")
            result["WhyNot100"].append("• Minimal page structure (no nav/content)")
            return result

        if len(soup.find_all("nav")) > 0 or \
           "blog" in body_text or \
           "product" in body_text or \
           len(soup.find_all("a")) > 5:
            result["Status"] = "🟢 Live Website"
            result["Confidence"] = 91
            result["Reasoning"].append("• Site has navigation, links, or product/blog content")
            result["WhyNot100"].append("• Some auto-generated content detected")
            return result

        if res.status_code in [200, 403, 404] and (not soup.body or len(body_text.strip()) < 100):
            result["Status"] = "🔒 Taken (No Site)"
            result["Confidence"] = 90
            result["Reasoning"].append("• Domain is registered but site shows no real content")
            result["WhyNot100"].append("• Could be misconfigured or intentionally blank")
            return result

        result["Reasoning"].append("• No clear indicators found in title/body")
        result["WhyNot100"].append("• Lacks nav or sale/brand keywords")

    except Exception as e:
        result["Reasoning"].append(f"• Error fetching domain: {str(e)}")

    return result


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    if request.method == "POST":
        domain = request.form["domain"]
        result = analyze_domain(domain)
    return render_template("index.html", result=result)


# if __name__ == "__main__":
#     app.run(debug=False, host='0.0.0.0', port=5000)

