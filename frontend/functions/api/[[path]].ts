const API_ORIGIN = "https://taiga-nova-api.onrender.com";

export const onRequest: PagesFunction = async ({ request }) => {
  const incomingUrl = new URL(request.url);
  const upstreamUrl = new URL(`${incomingUrl.pathname}${incomingUrl.search}`, API_ORIGIN);
  const headers = new Headers(request.headers);
  headers.delete("host");

  const upstreamRequest = new Request(upstreamUrl, {
    method: request.method,
    headers,
    body: request.body,
    redirect: "manual",
  });

  return fetch(upstreamRequest);
};
