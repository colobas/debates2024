// Define whitelisted origins
var whitelist = ["https://debates2024.info", "http://localhost:5173"];

// Check if the URI is listed in either the whitelist or blacklist
function isListed(uri, list) {
    return list.some(pattern => uri.match(pattern));
}

addEventListener("fetch", async event => {
    event.respondWith(handleRequest(event));
});

async function handleRequest(event) {
    const request = event.request;
    const isOPTIONS = request.method === "OPTIONS";
    const originUrl = new URL(request.url);
    const originHeader = request.headers.get("Origin");

    // Function to set or fix CORS headers
    function setCORSHeaders(headers) {
        headers.set("Access-Control-Allow-Origin", originHeader);
        if (isOPTIONS) {
            headers.set("Access-Control-Allow-Methods", request.headers.get("access-control-request-method"));
            const acrh = request.headers.get("access-control-request-headers");
            if (acrh) {
                headers.set("Access-Control-Allow-Headers", acrh);
            }
            headers.delete("X-Content-Type-Options");
        }
        return headers;
    }

    // Extract the URL to fetch from the query string
    const fetchUrl = decodeURIComponent(originUrl.search.substr(1));
    if (!isListed(originHeader, whitelist)) {
        return new Response("Not allowed by CORS", { status: 403 });
    }

    if (originUrl.search.startsWith("?")) {
        // Prepare the headers for the proxied request
        const proxiedRequestHeaders = new Headers();
        for (let [key, value] of request.headers) {
            if (!["origin", "referer", "cf-connecting-ip", "x-cors-headers"].includes(key.toLowerCase())) {
                proxiedRequestHeaders.append(key, value);
            }
        }

        try {
            const proxiedResponse = await fetch(fetchUrl, {
                method: request.method,
                //headers: proxiedRequestHeaders,
                redirect: 'follow',
                headers: {
                    'User-Agent': 'curl/8.1.2'
                }
            });

            // Copy the response headers to modify them
            let responseHeaders = new Headers(proxiedResponse.headers);
            responseHeaders = setCORSHeaders(responseHeaders);

            // Allow all received headers to be exposed to the client
            const exposedHeaders = [...responseHeaders.keys()].join(",");
            responseHeaders.set("Access-Control-Expose-Headers", exposedHeaders);

            const responseBody = isOPTIONS ? null : await proxiedResponse.arrayBuffer();

            return new Response(responseBody, {
                status: proxiedResponse.status,
                statusText: proxiedResponse.statusText,
                headers: responseHeaders
            });
        } catch (error) {
            return new Response("Error fetching the proxied request", { status: 500 });
        }
    } else {
        // Handle non-proxied requests (e.g., direct access to the worker script)
        console.log(originUrl);
        return new Response("This service is for CORS proxying only.", { status: 400 });
    }
}

