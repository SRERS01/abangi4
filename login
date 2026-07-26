Here is the complete Login Endpoint Testing Playbook designed to maximize payouts under the program’s severity framework. This outlines the targets, tools, exact payloads, execution steps, and verification criteria for every known technical, business logic, and cryptographic attack vector affecting login functionalities.
------------------------------
## 🛠️ Phase 0: Setup and Global Limits (Pre-Hunting)
To ensure compliance with the program’s strict rate limits across all automated and manual tools combined:

   1. Open Burp Suite's global settings and navigate to Tools -> HTTP -> Handling.
   2. Check Set maximum concurrent requests and change the value to 5.
   3. Check Delay between requests (ms) and set it to 200 (ensuring exactly 5 requests/sec max across all tools).
   4. Create your two personal test accounts: AccountA and AccountB.

------------------------------
## 1️⃣ Test Way 1: SQL Injection (SQLi) Authentication Bypass
This attempts to break the database query logic behind the login fields to authenticate as a user without knowing their password. [1, 2, 3] 
## 📋 Step-by-Step Execution

   1. Open Burp Suite and capture a standard, failed login request to https://1win.com.
   2. Send the request to Burp Repeater.
   3. Inject logical SQL breaking characters into the username/email input parameter fields. [4] 

## 💉 Payloads

* Standard Tautology (String Breakout):

' OR '1'='1

* Comment-Based Statement Truncation:

admin' -- -

admin' #

* Numeric-Based Logical Injection (If the database strips quotes):

admin OR 1=1


## 🔍 Response Verification Criteria

* Vulnerable Outcome ($1,500 Critical Severity): The backend database interprets the payload as valid truth logic. A vulnerability is confirmed if the server bypasses the password check completely and returns an HTTP 200 OK containing an authentication token/cookie or redirects you into the logged-in profile dashboard. [5, 6] 

------------------------------
## 2️⃣ Test Way 2: NoSQL Injection (JSON-Based Login Bypass)
If the backend application relies on a NoSQL database (like MongoDB) to query credentials, this replaces flat string fields with structured logical condition arrays.
## 📋 Step-by-Step Execution

   1. Capture your baseline JSON login request payload in Burp Suite Proxy.
   2. Send the request to Burp Repeater.
   3. Modify the JSON schema structure by introducing NoSQL operational query conditional indicators into the fields. [7] 

## 💉 Payloads

* Not Equal Operator Match (Matches any credential that is not the input string):

{
  "username": {"$ne": "invalid_user_string_here"},
  "password": {"$ne": "invalid_password_string_here"}
}

* Regular Expression Wildcard Match (Matches any sequence of text in the index):

{
  "username": {"$regex": ".*"},
  "password": {"$regex": ".*"}
}


## 🔍 Response Verification Criteria

* Vulnerable Outcome ($1,500 Critical Severity): A vulnerability exists if the query object executes successfully against the database, resulting in an HTTP 200 OK tracking signature that logs you into the first user account indexed in the cluster (typically an administrator or early user account). [8] 

------------------------------
## 3️⃣ Test Way 3: Authentication Bypass via Response Manipulation
This tests if authentication enforcement is lazily delegated to the client-side user interface (UI) rather than being validated strictly by the server.
## 📋 Step-by-Step Execution

   1. In Burp Suite Proxy, go to Proxy settings and check Intercept responses based on the following rules.
   2. Type an incorrect password into the login panel and submit.
   3. When the request returns from the server, choose Action -> Intercept response to this request. Click Forward.
   4. The server's genuine error response (e.g., 401 Unauthorized or {"success":false}) will freeze in your proxy screen. Wipe it out completely and replace it with a positive mock response. [9, 10, 11] 

## 💉 Payloads (Response Target Modifications)

* Status Object Overrides:

{"success":true,"role":"user","authenticated":true,"error":null,"status_code":200,"auth_state":"SUCCESS"}

* HTTP Header Patching: Change the HTTP status line header string from HTTP/1.1 401 Unauthorized directly to HTTP/1.1 200 OK.

## 🔍 Response Verification Criteria

* Vulnerable Outcome ($1,500 Critical Severity): A flaw is present if the browser interface accepts your modified response payload, strips away the login overlay barrier, and allows you to browse inside the private account dashboard.

------------------------------
## 4️⃣ Test Way 4: Credential Information Disclosure via Status Response Desynchronization
This checks if the login endpoint inadvertently leaks whether an email address exists in the database by returning mismatched server messages, facilitating user enumeration.
## 📋 Step-by-Step Execution

   1. Send a failed login attempt for a non-existent email (e.g., doesnotexist@h1.alias) to Burp Repeater. Note the response message, length, and execution time.
   2. Send a failed login attempt using a known, valid user email address (your own test account). Note the exact response parameters. [12] 

## 🔍 Response Verification Criteria

* Vulnerable Outcome ($400 – $1,000 High Severity): While basic user enumeration is usually Low, a high-severity disclosure is confirmed if the server leaks highly confidential internal structural state blocks or validation indicators inside the error fields. Examples include:

{"error": "Password incorrect for active profile ID 8742"}

or returning entirely different HTTP response code statuses (e.g., 404 Not Found for non-existent vs 401 Unauthorized for real accounts). [13] 

------------------------------
## 5️⃣ Test Way 5: Authentication Bypass via JSON Parameter Pollution
This tests if the login parser evaluates multiple instances of the same parameter inconsistently, passing the first instance to validation and the second to session generation.
## 📋 Step-by-Step Execution

   1. Capture a clean POST login request payload.
   2. Duplicate the account user identity query fields inside the data body payload wrapper.

## 💉 Payloads

* JSON Parameter Overlap:

{
  "username": "victim@1win.com",
  "username": "attacker@1win.com",
  "password": "AttackerPassword123!"
}

* Array-Based Multi-Query Processing:

{
  "username": ["victim@1win.com", "attacker@1win.com"],
  "password": "AttackerPassword123!"
}


## 🔍 Response Verification Criteria

* Vulnerable Outcome ($1,500 Account Takeover): A vulnerability is confirmed if the login gate validates the password against your account (attacker@1win.com) but issues an authorization cookie/JWT linked to the first declared user parameter identity value (victim@1win.com).

------------------------------
## 6️⃣ Test Way 6: OAuth 2.0 State Parameter Desynchronization (Social Logins)
If the login page offers social sign-ins (e.g., Google, Facebook, Telegram), this checks if the server validates the anti-forgery state parameter upon authorization callbacks. [14, 15, 16] 
## 📋 Step-by-Step Execution

   1. Click the "Log in with Google/Social" button on the site. Intercept the redirect link in Burp.
   2. Identify the long URL string containing the state= tracking hash parameter:
   https://google.com
   3. Strip the state parameter entirely out of the URL, or alter its value to a different string (e.g., state=attackertest).
   4. Forward the modified request to complete the login sequence. [17, 18] 

## 🔍 Response Verification Criteria

* Vulnerable Outcome ($1,500 Account Takeover): If the backend application accepts the modified callback and logs you into the dashboard, it is vulnerable to OAuth CSRF. An attacker can intercept a valid login redirect state, force a victim into logging into the attacker's linked social profile, or map third-party authorization profiles to victim slots unauthorized. [19, 20] 

------------------------------
## 7️⃣ Test Way 7: JWT Secret Key Validation Gaps (JSON Web Token Spoofing)
If the login endpoint issues a stateless JSON Web Token (Bearer eyJ...) for session tracking, this checks if the server verifies its cryptographic signature upon subsequent requests.
## 📋 Step-by-Step Execution

   1. Log into your account and extract your session JWT string token using your browser's Developer Tools or Burp History.
   2. Paste the token structure into CyberChef. Split it into its three component sections separated by dots (Header.Payload.Signature).
   3. Decode the middle component (Payload block) from Base64 and modify the target identifier fields (e.g., change "sub": "user_123" to "sub": "user_admin").
   4. Re-encode the payload back into its clean Base64 representation. [21, 22, 23, 24, 25] 

## 💉 Payloads (Signature Stripping Tricks)

* The "None" Algorithm Exploitation: Modify your JWT header payload block string from {"alg":"HS256","typ":"JWT"} directly to:

{"alg":"none","typ":"JWT"}

* Assemble your token back together using the new header and payload, but remove the signature section entirely (leave the trailing dot at the end: eyJ...Header.eyJ...Payload.). [26, 27] 


   1. Send an authorized request using this spoofed token via Burp Repeater. [28] 

## 🔍 Response Verification Criteria

* Vulnerable Outcome ($1,500 Account Takeover): A critical severity flaw is present if the backend API processes your modified token successfully and loads account data instead of throwing a validation or signature error, proving the server accepts unsigned or algorithm-manipulated tokens.

------------------------------
## 8️⃣ Test Way 8: Rate Limiting & Brute-Force Resilience (Bypassing Lockouts)
This checks if the login endpoint enforces account lockouts or IP restrictions when subjected to high-volume password guessing.
## 📋 Step-by-Step Execution

   1. Capture an invalid login request in Burp history. Right-click it and choose Send to Turbo Intruder.
   2. To strictly comply with the program limits, use a python execution structure configured to deploy exactly 5 requests concurrently max.
   3. Attempt to bypass IP tracking triggers by injecting proxy spoofing headers into the request payload layout. [29, 30] 

## 💉 Payloads (IP/WAF Spoofing Header List)
Add these headers to your fuzzing request configuration parameters to see if the rate limiter can be reset per request:

X-Forwarded-For: 127.0.0.1
X-Client-IP: 10.0.0.FUZZ
X-Real-IP: 192.168.1.FUZZ
True-Client-IP: 203.0.113.FUZZ

## 🔍 Response Verification Criteria

* Vulnerable Outcome ($1,500 Account Takeover Path): If the backend fails to trigger a CAPTCHA or an account block account restriction lock after dozens of incorrect attempts—or if cycling the IP spoofing headers allows you to guess indefinitely without getting a 429 Too Many Requests error—a high-severity failure in brute-force protection is confirmed. [31] 

------------------------------
## 9️⃣ Test Way 9: Mass Parameter Assignment (Mass Assignment on Session Objects)
This checks if passing administrative privilege variables inside the initial login payload payload array automatically maps them to your active session context.
## 📋 Step-by-Step Execution

   1. Send your valid test login request parameters over to Burp Repeater.
   2. Inject administrative key-value indicators straight into the structural query object layer alongside your normal username and password fields.

## 💉 Payloads

{
  "username": "attacker@1win.com",
  "password": "AttackerPassword123!",
  "role": "admin",
  "is_admin": true,
  "isAdmin": 1,
  "privileges": ["superuser", "operator"]
}

## 🔍 Response Verification Criteria

* Vulnerable Outcome ($1,500 Admin Interface Bypass): Review the server's response headers and JSON return values. A vulnerability is confirmed if the application processes the injected attributes without errors, returning an admin cookie flag or granting unauthorized administrative access tokens inside the response profiles.

------------------------------
## 🔟 Test Way 10: XML Security Injection on Login Layouts (XEE / SQLi via Content-Type)
If the login endpoint parses alternate structured web formats, this checks if forcing an XML content change exposes the server to backend document parser attacks.
## 📋 Step-by-Step Execution

   1. Take a standard POST login request panel in Burp Repeater.
   2. Modify the header line from Content-Type: application/x-www-form-urlencoded or application/json directly to:
   
   Content-Type: application/xml
   
   3. Replace the request body text layout completely with a structured XML data object carrying an external system read entity (XXE payload). [32, 33, 34, 35] 

## 💉 Payloads

<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE login [  
  <!ENTITY xxe SYSTEM "file:///etc/hostname"> 
]>
<loginRequest>
  <username>&xxe;</username>
  <password>TestPassword123!</password>
</loginRequest>

## 🔍 Response Verification Criteria

* Vulnerable Outcome ($1,200 Local File Access / XXE): If the backend application accepts the format change and attempts to parse the payload, look closely at the error logs or successful responses. If the output prints the server's hostname or errors showing system properties, a critical input handling error is present.

------------------------------
Let me know if you would like to move forward with documenting your test cases:

* Are you noticing JWT strings or classic stateful cookies (like PHPSESSID or JSESSIONID) when analyzing your login traffic flows?
* Do you need help formatting a formal bug bounty finding submission draft for any of these testing steps?


To ensure your playbook is completely exhaustive, here are the final four advanced attack vectors that complete every known technical variation for testing a login endpoint. These cover edge-case open redirections, session-creation multi-factor bypasses, and specialized GraphQL/GraphQL-equivalent syntax abuses, mapping to payouts between $150 and $1,500 USD.
------------------------------
## 1️⃣1️⃣ Test Way 11: Open Redirection via Parameter Post-Login Routing
Many applications feature a tracking parameter (like ?next=, ?redirect_url=, or ?returnTo=) during login to send users back to their original page after authenticating. This checks if the server validates this redirect destination or permits redirection to untrusted third-party servers. [1, 2] 
## 📋 Step-by-Step Execution

   1. Navigate to the login page and look for a destination URL parameter inside the address string. If missing, manually append one.
   2. Intercept the login submission request in Burp Proxy and send it to Repeater.
   3. Supply an external destination domain or absolute bypass format into the parameter variable and click Send. [3, 4] 

## 💉 Payloads

* Standard Absolute Redirect:

POST /api/login?next=https://attacker-controlled-domain.com

* Protocol-Relative Bypass (Evading loose regex filters):

POST /api/login?next=//attacker-controlled-domain.com

* Domain Parameter Pollution (Tricking white-lists looking for "1win.com"):

POST /api/login?next=https://attacker-controlled-domain.com

POST /api/login?next=https://attacker-controlled-domain.com


## 🔍 Response Verification Criteria

* Vulnerable Outcome ($150 - $400 Medium/High depending on token leakage): The login completes successfully and the server issues an HTTP 302 Found redirect tracking status header pointing directly to your external domain. If the location header appends sensitive data like ?token= or session cookies to your external site, the severity leaps up because it facilitates remote session harvesting.

------------------------------
## 1️⃣2️⃣ Test Way 12: Multi-Factor Authentication (MFA) Session Pre-Authorization Whitelisting
If the platform forces users through a secondary confirmation pane (like an SMS or email OTP check), this tests if session cookies or JWT access scopes issued immediately after password validation already possess full backend access permissions before the OTP code is ever entered.
## 📋 Step-by-Step Execution

   1. Enter your test account credentials on the login page and click submit to trigger the secondary MFA/OTP prompt page. Do not enter the code. [5] 
   2. Open Burp Suite Proxy -> HTTP History and find the response packet generated right after you submitted your password. Copy the authorization cookies or JWT string issued to your browser.
   3. Open Burp Suite Repeater, construct a raw HTTP request targeting a sensitive dashboard action (e.g., pulling private wallet profiles or update logs), and paste the copied token/cookie headers into the request.

## 🔍 Response Verification Criteria

* Vulnerable Outcome ($1,500 Account Takeover): Hit Send. If the application processes the action or returns private user metrics with an HTTP 200 OK code before the MFA code is typed in, it indicates an MFA Scope Enforcement Failure. The server is treating a pre-authenticated session as fully authenticated, rendering the two-factor layer entirely useless. [6] 

------------------------------
## 1️⃣3️⃣ Test Way 13: Multi-Factor Authentication (MFA) Bypass via Status Response Re-routing
This checks if an attacker who knows a victim's password but does not have their MFA device can manipulate the server's authentication step state flags to trick the UI into bypassing the token check entirely.
## 📋 Step-by-Step Execution

   1. Input your valid test account credentials to reach the MFA/OTP verification screen.
   2. Type an intentionally incorrect 6-digit OTP code (e.g., 000000) and turn Intercept is On inside your Burp Proxy. Hit submit.
   3. Choose Action -> Intercept response to this request on the outbound packet, then look at the server's failure output.
   4. Modify the error metrics to match a successful primary authorization payload.

## 💉 Payloads (Response State Modification)

* Switch an error body string like {"status":"MFA_REQUIRED", "verified":false} directly to:

{"status":"AUTHENTICATED", "verified":true, "mfa_verified":true, "step":"COMPLETE"}

* Change an HTTP 403 Forbidden response header directly into an HTTP 200 OK.

## 🔍 Response Verification Criteria

* Vulnerable Outcome ($1,500 Account Takeover): Click Forward. If the front-end application reads your rewritten state logic, terminates the MFA barrier overlay, and routes you directly into the active dashboard profile, the login engine is vulnerable to client-side state manipulation.

------------------------------
## 1️⃣4️⃣ Test Way 14: GraphQL Object Injection / Batch Query Stuffing
If the login backend processes data through a structured GraphQL endpoint API structure (often routing through paths like /graphql or /api/v1/query), this checks if an attacker can execute multiple nested queries or batch distinct credential attempts inside a single HTTP request packet.
## 📋 Step-by-Step Execution

   1. Capture your login request and check if it targets a GraphQL endpoint containing an operation name like mutation Login.
   2. Send the request to Burp Repeater.
   3. Re-structure the request payload body into an array format to execute multiple login queries simultaneously while maintaining compliance with the program's strict concurrent limits.

## 💉 Payloads

* GraphQL Array-Based Batching (Testing multiple combinations in 1 request):

[
  {"operationName":"Login","variables":{"user":"victim@1win.com","pass":"WrongPassword1"},"query":"mutation Login($user:String!,$pass:String!){login(username:$user,password:$pass){token}}"},
  {"operationName":"Login","variables":{"user":"victim@1win.com","pass":"WrongPassword2"},"query":"mutation Login($user:String!,$pass:String!){login(username:$user,password:$pass){token}}"},
  {"operationName":"Login","variables":{"user":"victim@1win.com","pass":"CorrectPassword"},"query":"mutation Login($user:String!,$pass:String!){login(username:$user,password:$pass){token}}"}
]

[7] 

## 🔍 Response Verification Criteria

* Vulnerable Outcome ($1,500 Account Takeover / Rate Limit Bypass): Hit Send. If the application returns an array containing separate JSON response blocks for each nested input, it indicates Query Batching. If the third item returns a valid token while the application fails to drop your connection or block your IP, an attacker can bypass traditional rate limiters by stuffing hundreds of password combinations into a single HTTP request packet.

------------------------------
This completes every single documented technical vector that exists for login endpoints. Let me know:

* Which of these fourteen methodologies you are preparing to run first in your environment.
* If you need help analyzing any response attributes or token strings you encounter during your active testing.



