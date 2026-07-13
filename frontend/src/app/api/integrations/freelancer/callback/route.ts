import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const code = searchParams.get("code");
  const state = searchParams.get("state");
  const error = searchParams.get("error");
  const errorDescription = searchParams.get("error_description");

  const frontendUrl = process.env.NEXT_PUBLIC_FRONTEND_URL || "http://localhost:3000";

  if (error) {
    const errorMsg = errorDescription || error;
    const html = `
      <!DOCTYPE html>
      <html>
      <head><title>Authentication Failed</title></head>
      <body style="font-family: system-ui; padding: 2rem; text-align: center;">
        <h1 style="color: #dc2626;">Authentication Failed</h1>
        <p>${errorMsg}</p>
        <button onclick="window.close()" style="margin-top: 1rem; padding: 0.5rem 1rem;">Close Window</button>
      </body>
      </html>
    `;
    return new NextResponse(html, { headers: { "Content-Type": "text/html" } });
  }

  if (!code || !state) {
    const html = `
      <!DOCTYPE html>
      <html>
      <head><title>Authentication Failed</title></head>
      <body style="font-family: system-ui; padding: 2rem; text-align: center;">
        <h1 style="color: #dc2626;">Authentication Failed</h1>
        <p>Missing authorization code or state parameter.</p>
        <button onclick="window.close()" style="margin-top: 1rem; padding: 0.5rem 1rem;">Close Window</button>
      </body>
      </html>
    `;
    return new NextResponse(html, { headers: { "Content-Type": "text/html" } });
  }

  // Success - send the code to the opener window via postMessage
  const html = `
    <!DOCTYPE html>
    <html>
    <head><title>Authentication Successful</title></head>
    <body style="font-family: system-ui; padding: 2rem; text-align: center;">
      <h1 style="color: #16a34a;">Authentication Successful</h1>
      <p>You can now close this window.</p>
      <script>
        // Send the authorization code to the opener window
        if (window.opener) {
          window.opener.postMessage({
            type: 'FREELANCER_OAUTH_CALLBACK',
            code: '${code}',
            state: '${state}'
          }, '${frontendUrl}');
        }
        // Close the popup after a short delay
        setTimeout(() => window.close(), 1000);
      </script>
      <button onclick="window.close()" style="margin-top: 1rem; padding: 0.5rem 1rem;">Close Window</button>
    </body>
    </html>
  `;
  return new NextResponse(html, { headers: { "Content-Type": "text/html" } });
}