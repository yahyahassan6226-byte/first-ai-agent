"use strict";


// =========================================================
// CONFIG
// =========================================================

const API_BASE_URL =
    "http://127.0.0.1:8000";


// =========================================================
// STATE
// =========================================================

let threadId =
    null;


let requestInProgress =
    false;


// =========================================================
// DOM ELEMENTS
// =========================================================

const chatForm =
    document.getElementById(
        "chat-form"
    );


const messageInput =
    document.getElementById(
        "message-input"
    );


const sendButton =
    document.getElementById(
        "send-button"
    );


const messagesContainer =
    document.getElementById(
        "messages"
    );


const apiStatus =
    document.getElementById(
        "api-status"
    );


const threadElement =
    document.getElementById(
        "thread-id"
    );


const streamStatus =
    document.getElementById(
        "stream-status"
    );


const newChatButton =
    document.getElementById(
        "new-chat-button"
    );


// =========================================================
// SCROLL
// =========================================================

function scrollToBottom() {

    messagesContainer.scrollTop =
        messagesContainer.scrollHeight;
}


// =========================================================
// CREATE MESSAGE
// =========================================================

function createMessage(
    role,
    content = ""
) {

    const messageElement =
        document.createElement(
            "div"
        );


    messageElement.classList.add(
        "message",
        role
    );


    const roleElement =
        document.createElement(
            "div"
        );


    roleElement.classList.add(
        "message-role"
    );


    if (role === "user") {

        roleElement.textContent =
            "You";

    } else if (
        role === "assistant"
    ) {

        roleElement.textContent =
            "Agent";

    } else {

        roleElement.textContent =
            "System";
    }


    const contentElement =
        document.createElement(
            "div"
        );


    contentElement.classList.add(
        "message-content"
    );


    contentElement.textContent =
        content;


    messageElement.appendChild(
        roleElement
    );


    messageElement.appendChild(
        contentElement
    );


    messagesContainer.appendChild(
        messageElement
    );


    scrollToBottom();


    return {
        element:
            messageElement,

        content:
            contentElement,
    };
}


// =========================================================
// ADD MESSAGE
// =========================================================

function addMessage(
    role,
    content
) {

    return createMessage(
        role,
        content
    );
}


// =========================================================
// THREAD
// =========================================================

function setThreadId(
    newThreadId
) {

    if (!newThreadId) {
        return;
    }


    threadId =
        newThreadId;


    threadElement.textContent =
        newThreadId;
}


// =========================================================
// API STATUS
// =========================================================

function setApiStatus(
    status,
    text
) {

    apiStatus.classList.remove(
        "checking",
        "online",
        "offline"
    );


    apiStatus.classList.add(
        status
    );


    apiStatus.textContent =
        text;
}


// =========================================================
// STREAM STATUS
// =========================================================

function setStreamStatus(
    visible,
    text = "Agent is responding..."
) {

    streamStatus.textContent =
        text;


    if (visible) {

        streamStatus.classList.remove(
            "hidden"
        );

    } else {

        streamStatus.classList.add(
            "hidden"
        );
    }
}


// =========================================================
// HEALTH CHECK
// =========================================================

async function checkApiHealth() {

    setApiStatus(
        "checking",
        "Checking API..."
    );


    try {

        const response =
            await fetch(
                `${API_BASE_URL}/health`
            );


        if (!response.ok) {

            throw new Error(
                `HTTP ${response.status}`
            );
        }


        setApiStatus(
            "online",
            "API Online"
        );


        return true;

    } catch (error) {

        console.error(
            "Health check failed:",
            error
        );


        setApiStatus(
            "offline",
            "API Offline"
        );


        return false;
    }
}


// =========================================================
// PARSE NORMAL HTTP ERROR
// =========================================================

async function parseErrorResponse(
    response
) {

    try {

        const data =
            await response.json();


        if (
            data.error
            &&
            data.error.message
        ) {

            return data.error.message;
        }


        if (
            typeof data.detail ===
            "string"
        ) {

            return data.detail;
        }


        if (
            Array.isArray(
                data.detail
            )
        ) {

            return data.detail
                .map(
                    item =>
                        item.msg
                        || JSON.stringify(
                            item
                        )
                )
                .join(", ");
        }


        return JSON.stringify(
            data
        );

    } catch {

        return (
            `Request failed with `
            + `HTTP ${response.status}`
        );
    }
}


// =========================================================
// PROCESS STREAM EVENT
// =========================================================

function processStreamEvent(
    eventData,
    assistantMessage
) {

    if (
        !eventData
        ||
        !eventData.type
    ) {

        return;
    }


    // -----------------------------------------------------
    // THREAD EVENT
    // -----------------------------------------------------

    if (
        eventData.type ===
        "thread"
    ) {

        setThreadId(
            eventData.thread_id
        );

        return;
    }


    // -----------------------------------------------------
    // CHUNK EVENT
    // -----------------------------------------------------

    if (
        eventData.type ===
        "chunk"
    ) {

        const incomingContent =
            String(
                eventData.content
                || ""
            );


        const currentContent =
            assistantMessage
                .content
                .textContent;


        /*
        LangGraph state streaming-ka hadda wuxuu mararka qaar
        soo celin karaa answer-ka oo dhan halkii uu delta yar
        ka soo celin lahaa.

        Haddii chunk cusub uu ka bilaabmo text-kii hore:
        replace garee.

        Haddii kale:
        append garee.
        */

        if (
            currentContent
            &&
            incomingContent.startsWith(
                currentContent
            )
        ) {

            assistantMessage
                .content
                .textContent =
                    incomingContent;

        } else {

            assistantMessage
                .content
                .textContent +=
                    incomingContent;
        }


        scrollToBottom();

        return;
    }


    // -----------------------------------------------------
    // ERROR EVENT
    // -----------------------------------------------------

    if (
        eventData.type ===
        "error"
    ) {

        throw new Error(
            eventData.message
            || "Streaming failed."
        );
    }


    // -----------------------------------------------------
    // DONE EVENT
    // -----------------------------------------------------

    if (
        eventData.type ===
        "done"
    ) {

        if (
            eventData.thread_id
        ) {

            setThreadId(
                eventData.thread_id
            );
        }
    }
}


// =========================================================
// STREAM CHAT REQUEST
// =========================================================

async function streamChatRequest(
    message,
    assistantMessage
) {

    const payload = {
        message:
            message,
    };


    if (threadId) {

        payload.thread_id =
            threadId;
    }


    const response =
        await fetch(
            `${API_BASE_URL}/chat/stream`,
            {
                method:
                    "POST",

                headers: {
                    "Content-Type":
                        "application/json",
                },

                body:
                    JSON.stringify(
                        payload
                    ),
            }
        );


    if (!response.ok) {

        const errorMessage =
            await parseErrorResponse(
                response
            );


        throw new Error(
            errorMessage
        );
    }


    if (!response.body) {

        throw new Error(
            "Browser-ku streaming response body ma helin."
        );
    }


    // Response.body waa ReadableStream.
    const reader =
        response.body.getReader();


    // Network bytes → UTF-8 text.
    const decoder =
        new TextDecoder(
            "utf-8"
        );


    let buffer =
        "";


    try {

        while (true) {

            const {
                value,
                done,
            } =
                await reader.read();


            if (done) {
                break;
            }


            buffer +=
                decoder.decode(
                    value,
                    {
                        stream:
                            true,
                    }
                );


            /*
            Backend-ku wuxuu isticmaalaa NDJSON:
            hal JSON object line kasta.
            */

            const lines =
                buffer.split(
                    "\n"
                );


            /*
            Line-ka ugu dambeeya waxaa laga yaabaa
            inuusan wali dhammeystirnayn.
            */

            buffer =
                lines.pop()
                || "";


            for (
                const rawLine
                of lines
            ) {

                const line =
                    rawLine.trim();


                if (!line) {
                    continue;
                }


                try {

                    const eventData =
                        JSON.parse(
                            line
                        );


                    processStreamEvent(
                        eventData,
                        assistantMessage
                    );

                } catch (error) {

                    console.error(
                        "Invalid stream line:",
                        line,
                        error
                    );
                }
            }
        }


        /*
        Decoder-ka bytes haray ka soo saar.
        */

        buffer +=
            decoder.decode();


        const finalLine =
            buffer.trim();


        if (finalLine) {

            try {

                const eventData =
                    JSON.parse(
                        finalLine
                    );


                processStreamEvent(
                    eventData,
                    assistantMessage
                );

            } catch (error) {

                console.error(
                    "Invalid final stream line:",
                    finalLine,
                    error
                );
            }
        }

    } finally {

        reader.releaseLock();
    }
}


// =========================================================
// LOADING STATE
// =========================================================

function setLoading(
    loading
) {

    requestInProgress =
        loading;


    sendButton.disabled =
        loading;


    messageInput.disabled =
        loading;


    newChatButton.disabled =
        loading;


    sendButton.textContent =
        loading
            ? "Streaming..."
            : "Send";


    setStreamStatus(
        loading
    );
}


// =========================================================
// HANDLE SUBMIT
// =========================================================

async function handleSubmit(
    event
) {

    event.preventDefault();


    if (
        requestInProgress
    ) {

        return;
    }


    const message =
        messageInput
            .value
            .trim();


    if (!message) {
        return;
    }


    // User bubble.
    addMessage(
        "user",
        message
    );


    messageInput.value =
        "";


    // Empty assistant bubble.
    const assistantMessage =
        createMessage(
            "assistant",
            ""
        );


    assistantMessage
        .element
        .classList
        .add(
            "streaming"
        );


    setLoading(
        true
    );


    try {

        await streamChatRequest(
            message,
            assistantMessage
        );


        assistantMessage
            .element
            .classList
            .remove(
                "streaming"
            );


        if (
            !assistantMessage
                .content
                .textContent
                .trim()
        ) {

            assistantMessage
                .content
                .textContent =
                    "Agent-ku jawaab ma soo celin.";
        }


        setApiStatus(
            "online",
            "API Online"
        );

    } catch (error) {

        console.error(
            "Streaming request failed:",
            error
        );


        assistantMessage
            .element
            .classList
            .remove(
                "streaming"
            );


        assistantMessage
            .element
            .classList
            .remove(
                "assistant"
            );


        assistantMessage
            .element
            .classList
            .add(
                "error"
            );


        assistantMessage
            .content
            .textContent =
                error.message
                || "Streaming failed.";


        await checkApiHealth();

    } finally {

        setLoading(
            false
        );


        scrollToBottom();


        messageInput.focus();
    }
}


// =========================================================
// ENTER KEY
// =========================================================

function handleKeyDown(
    event
) {

    if (
        event.key ===
            "Enter"
        &&
        !event.shiftKey
    ) {

        event.preventDefault();


        chatForm.requestSubmit();
    }
}


// =========================================================
// NEW CHAT
// =========================================================

function startNewChat() {

    if (
        requestInProgress
    ) {

        return;
    }


    threadId =
        null;


    threadElement.textContent =
        "New conversation";


    messagesContainer.innerHTML =
        "";


    addMessage(
        "assistant",
        (
            "Salaan! Conversation cusub "
            + "ayaa bilaabatay. "
            + "Maxaan kaa caawin karaa?"
        )
    );


    messageInput.focus();
}


// =========================================================
// EVENTS
// =========================================================

chatForm.addEventListener(
    "submit",
    handleSubmit
);


messageInput.addEventListener(
    "keydown",
    handleKeyDown
);


newChatButton.addEventListener(
    "click",
    startNewChat
);


// =========================================================
// START APPLICATION
// =========================================================

async function startApp() {

    await checkApiHealth();


    messageInput.focus();
}


startApp();