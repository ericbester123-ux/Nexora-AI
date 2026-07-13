import { NextRequest, NextResponse } from "next/server";

function renderPage(title: string, heading: string, message: string, isError: boolean) {
  const color = isError ? "#dc2626" : "#16a34a";
  return `<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>${title}</title></head>
<body style="font-family: system-ui; padding: 2rem; text-align: center;">
  <h1 style="color: ${color};">${heading}</h1>
  <p>${message}</p>
  <button onclick="window.close()" style="margin-top: 1rem; padding: 0.5rem 1rem;">Close Window</button>
</body>
</html>`;
}

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const code = searchParams.get("code");
  const state = searchParams.get("state");
  const error = searchParams.get("error");
  const errorDescription = searchParams.get("error_description");

  if (error) {
    return new NextResponse(
      renderPage("Authentication Failed", "Authentication Failed", errorDescription || error, true),
      { headers: { "Content-Type": "text/html" } },
    );
  }

  if (!code || !state) {
    return new NextResponse(
      renderPage("Authentication Failed", "Authentication Failed", "Missing authorization code or state parameter.", true),
      { headers: { "Content-Type": "text/html" } },
    );
  }

  const safeCode = JSON.stringify(code);
  const safeState = JSON.stringify(state);

  const html = `<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Authentication Successful</title></head>
<body style="font-family: system-ui; padding: 2rem; text-align: center;">
  <h1 style="color: #16a34a;">Authentication Successful</h1>
  <p>You can now close this window.</p>
  <script>
    if (window.opener) {
      window.opener.postMessage({
        type: 'FREELANCER_OAUTH_CALLBACK',
        code: ${safeCode},
        state: ${safeState}
      }, window.location.origin);
    }
    setTimeout(function() { window.close(); }, 1000);
  </script>
</body>
</html>`;

  return new NextResponse(html, { headers: { "Content-Type": "text/html" } });
}