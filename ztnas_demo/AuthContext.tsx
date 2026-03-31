import React, { createContext, useState, useContext } from 'react';
import { useAppContext } from './AppContext';
import type { AuthContextType, User } from './types';

const AuthContext = createContext<AuthContextType | null>(null);

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const { users, updateUser } = useAppContext();
    const [currentUser, setCurrentUser] = useState<User | null>(null);
    const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);

    const login = async (email: string, password?: string): Promise<User> => {
        const user = users.find(u => u.email.toLowerCase() === email.toLowerCase());

        if (!user) {
            throw new Error('Invalid email or password.');
        }

        // For new users, we only check for their existence. The flow continues in LoginView.
        if (user.needsOnboarding) {
            return user;
        }

        // For existing users, we check the password.
        if (!password || user.password !== password) {
            throw new Error('Invalid email or password.');
        }

        return user;
    };
    
    // This is called by the LoginView after MFA or onboarding is successful.
    const setAuthenticatedState = (user: User) => {
        setCurrentUser(user);
        setIsAuthenticated(true);
    };

    const logout = () => {
        setCurrentUser(null);
        setIsAuthenticated(false);
    };

    const completeOnboarding = async (userId: string, password_raw: string): Promise<User> => {
        const user = users.find(u => u.id === userId);
        if (user) {
            const updatedUser: User = {
                ...user,
                password: password_raw,
                needsOnboarding: false,
            };
            updateUser(updatedUser);
            return updatedUser;
        }
        throw new Error("User not found during onboarding completion");
    };
    
    const contextValue: AuthContextType = {
        currentUser,
        isAuthenticated,
        login,
        logout,
        completeOnboarding,
        setAuthenticatedState,
    };

    return (
        <AuthContext.Provider value={contextValue}>
            {children}
        </AuthContext.Provider>
    );
};