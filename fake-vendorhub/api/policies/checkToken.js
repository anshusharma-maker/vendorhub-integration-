module.exports = function (req, res, next) {

    const authHeader = req.headers.authorization;

    if (!authHeader) {
        return res.status(401).json({
            error: 'Authorization token is required'
        });
    }

    const parts = authHeader.split(' ');

    if (parts.length !== 2 || parts[0] !== 'Bearer') {
        return res.status(401).json({
            error: 'Invalid Authorization header'
        });
    }

    const token = parts[1];

    if (!TokenService.isValid(token)) {
        return res.status(401).json({
            error: 'Invalid or expired token'
        });
    }

    return next();
};