async function apiRequest(url, options = {}) {
    const response = await fetch(url, options);

    if (response.status === 204) {
        return null;
    }

    let data;

    try {
        data = await response.json();
    } catch {
        throw new Error(
            `Unexpected server response (${response.status}).`
        );
    }

    if (!response.ok) {
        throw new Error(
            data.error?.message ||
            `Request failed (${response.status}).`
        );
    }

    return data;
}


async function apiGet(url) {
    return apiRequest(url);
}


window.PlanitAPI = {
    get: apiGet,
};