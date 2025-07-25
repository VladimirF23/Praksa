// Frontend/my-app/src/utils/AuthError.js
class AuthError extends Error {
    constructor(message, status = null) {
        super(message);
        this.name = 'AuthError';
        this.status = status;
    }
}
export default AuthError;