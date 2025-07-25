// AccessDeniedPage.jsx
import React from 'react';
import { Link } from 'react-router-dom';

const AccessDeniedPage = () => {
    return (
        <div className="flex flex-col items-center justify-center min-h-[calc(100vh-64px)] text-gray-800">
            <h1 className="text-4xl font-bold mb-4">403 - Access Denied</h1>
            <p className="text-xl mb-8">You do not have permission to view this page.</p>
            <Link to="/" className="text-blue-600 hover:underline">Go to Home Page</Link>
        </div>
    );
};

export default AccessDeniedPage;