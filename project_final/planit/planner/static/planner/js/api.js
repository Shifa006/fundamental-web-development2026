function getCookie(name) {
    const cookies =
        document.cookie
            .split(";")
            .map((cookie) =>
                cookie.trim()
            );

    for (const cookie of cookies) {
        if (
            cookie.startsWith(
                `${name}=`
            )
        ) {
            return decodeURIComponent(
                cookie.slice(
                    name.length + 1
                )
            );
        }
    }

    return null;
}


async function apiRequest(
    url,
    {
        method = "GET",
        data = null,
    } = {},
) {
    const headers = {
        Accept: "application/json",
    };


    if (data !== null) {
        headers["Content-Type"] =
            "application/json";
    }


    const unsafe =
        ![
            "GET",
            "HEAD",
            "OPTIONS",
        ].includes(method);


    if (unsafe) {
        const token =
            getCookie(
                "csrftoken"
            );

        if (token) {
            headers[
                "X-CSRFToken"
            ] = token;
        }
    }


    const options = {
        method,
        headers,
        credentials:
            "same-origin",
    };


    if (data !== null) {
        options.body =
            JSON.stringify(data);
    }


    const response =
        await fetch(
            url,
            options
        );


    if (
        response.status
        === 204
    ) {
        return null;
    }


    let result;

    try {
        result =
            await response.json();
    } catch {
        throw new Error(
            `Unexpected server response (${response.status}).`
        );
    }


    if (!response.ok) {
        const error =
            new Error(
                result.error?.message
                || `Request failed (${response.status}).`
            );

        error.code =
            result.error?.code;

        error.field =
            result.error?.field;

        error.status =
            response.status;

        throw error;
    }


    return result;
}


function get(url) {
    return apiRequest(
        url
    );
}


function post(
    url,
    data,
) {
    return apiRequest(
        url,
        {
            method: "POST",
            data,
        }
    );
}


function patch(
    url,
    data,
) {
    return apiRequest(
        url,
        {
            method: "PATCH",
            data,
        }
    );
}


function remove(url) {
    return apiRequest(
        url,
        {
            method: "DELETE",
        }
    );
}


window.PlanitAPI = {
    get,
    post,
    patch,
    delete: remove,
};