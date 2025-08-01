export const retryAsyncFn = async (fn: any, retry: number) => {
    try {
        await fn()
    } catch (e) {
        if (retry > 0) {
            setTimeout(async () => {
                await retryAsyncFn(fn, retry - 1)
            }, 500)
        } else {
            throw e
        }
    }
}

export const retryFn = (fn: any, retry: number) => {
    try {
        fn()
    } catch (e) {
        if (retry > 0) {
            setTimeout(() => {
                retryFn(fn, retry - 1)
            }, 500)
        } else {
            throw e
        }
    }
}
