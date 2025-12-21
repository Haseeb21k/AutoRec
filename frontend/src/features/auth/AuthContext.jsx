import React, { createContext, useState, useContext, useEffect } from 'react';
import apiClient from '@/api/client';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    // Helper: Decode JWT to get user info (email & role)
    const getUserFromToken = (token) => {
        try {
            // JWT is "Header.Payload.Signature". We grab the Payload.
            const base64Url = token.split('.')[1];
            const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
            const jsonPayload = decodeURIComponent(window.atob(base64).split('').map(function (c) {
                return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
            }).join(''));

            const payload = JSON.parse(jsonPayload);
            // Backend sends: { sub: email, role: role, exp: ... }
            return { email: payload.sub, role: payload.role };
        } catch (e) {
            return null;
        }
    };

    useEffect(() => {
        // Check both storages
        const token = localStorage.getItem('token') || sessionStorage.getItem('token');
        if (token) {
            const userData = getUserFromToken(token);
            if (userData) {
                setUser(userData);
                apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
            } else {
                localStorage.removeItem('token');
                sessionStorage.removeItem('token');
            }
        }
        setLoading(false);
    }, []);

    const login = async (email, password, rememberMe = false) => {
        const formData = new FormData();
        formData.append('username', email);
        formData.append('password', password);
        formData.append('remember_me', rememberMe);

        const res = await apiClient.post('/auth/token', formData, {
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        });

        const { access_token } = res.data;

        // Save token based on preference
        if (rememberMe) {
            localStorage.setItem('token', access_token);
        } else {
            sessionStorage.setItem('token', access_token);
        }

        apiClient.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;

        // Decode token to get REAL role
        const userData = getUserFromToken(access_token);
        setUser(userData);

        return true;
    };

    const logout = () => {
        localStorage.removeItem('token');
        sessionStorage.removeItem('token');
        delete apiClient.defaults.headers.common['Authorization'];
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ user, login, logout, loading }}>
            {!loading && children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);