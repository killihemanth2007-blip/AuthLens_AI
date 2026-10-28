# AuthLens Market API-key monitor prototype

This project is a local online-store simulation with a backend integration monitor. The shopper browses fictional products and places a simulated order. Immediately after checkout, the backend can deliberately change its fake partner API credential. The app then makes a request to a built-in mock partner endpoint, detects the invalid credential response, and changes the interface to show the alert and safe key fingerprints.

## Run locally in VS Code on Windows

Requires Python 3.10 or newer and the Microsoft Python extension in VS Code.

1. Open this project folder in VS Code.
2. Choose Terminal → New Terminal.
3. Create a project environment:
   
       py -m venv .venv

4. Install Flask:
   
       .\.venv\Scripts\python.exe -m pip install -r requirements.txt

5. Start the site:
   
       .\.venv\Scripts\python.exe app.py

6. Open http://127.0.0.1:5000 in a browser. Leave the terminal open while the site is running. Stop with Ctrl+C.

## Expo demonstration

1. Add one product to the cart.
2. Leave “Simulate backend API-key change immediately after booking” checked.
3. Place the demo order. The order is recorded locally, then the app changes its fake backend key and tries a mock partner API call.
4. Show the interface change: the order remains placed, but partner confirmation fails. AuthLens reports HTTP 401 and shows expected versus active key fingerprints. It never displays the credential.
5. Click “Restore demo key & retry.” The app restores the fake key and retries the request; the interface should report success.
6. Uncheck the simulation option and place another order to show the normal successful flow.

## What the demo means

In a real integration, a credential can become invalid or misconfigured, causing partner API requests to fail. A monitoring system can detect signals such as unauthorized responses and credential-version mismatches, then alert an operator. This prototype demonstrates that workflow with a local mock service.

Amazon's Selling Partner API uses an authorization workflow based on Login with Amazon (OAuth 2.0) and related credentials; this prototype is not an Amazon integration. See Amazon's official [SP-API onboarding overview](https://developer-docs.amazon.com/sp-api/docs/onboarding-overview).

## Important safety and scope limits

- Product orders, prices, credentials, and partner responses are fictional. Checkout never takes payment.
- The mock partner API runs inside this app; it makes no external network requests.
- The credential is deliberately changed only as a demo fault injection. The site displays short fingerprints, not the fake key value.
- Never put real API keys in frontend JavaScript or publish real credentials. A production app should store secrets in server-side secret management, monitor responses, rotate credentials through the provider's supported process, and avoid logging secret values.
- This is a rule-based monitoring prototype, not an AI model or production-grade security scanner.
- Orders and event logs are held in memory and reset when the server stops.
