


// src/services/authService.js
import {loginUser,registerUser ,logoutUser,fetchUserDetails} from "../api/authApi";
import { 
    loginSuccess, 
    loginFailure, 
    clearAuthError, 
    logout 
} from "../features/authorization/authSlice"; 



// Ova funkcija orkestrira ceo proces logout iz aplikacije, poziva stvari iz api-a i updajetuje redux state
export const handleLogout = async (dispatch, navigate) => {
    try {
        // 1. Pozovi backend API
        await logoutUser(); 

        // 2. Azuriraj Redux stanje (ocisti podatke klijenta)
        dispatch(logout()); 

        // 3. Navigiraj korisnika na pocetnu stranicu
        navigate('/');       
    } catch (error) {
        console.error("Logout failed:", error);
        
        // U slucaju greške (npr. backend nedostupan), 
        // i dalje osiguravamo da je client-side state ociscen
        dispatch(logout()); 
        navigate('/'); 
        
        // Opcionalno: Mozemo ovde dodati logiku za globalnu notifikaciju o grešci
    }
};

// Nova funkcija za rukovanje  procesom prijavljivanja
export const handleLogin = async (credentials, dispatch, navigate) => {
    
    dispatch(clearAuthError()); 

    try {
        // 1. Poziv API-ju za postavljanje HTTPOnly kolacica
        await loginUser(credentials);
        
        // 2. Poziv API-ju za dohvat podataka o korisniku - SADA KROZ ENKAPSULIRANU FUNKCIJU
        const userDetails = await fetchUserDetails();
        // Nema potrebe za userDetailsResponse

        console.log("DEBUG SERVICE: userDetails before dispatch", userDetails);

        // 3. Azuriranje Redux stanja
        dispatch(loginSuccess(userDetails));

        // 4. Navigacija
        navigate('/');

    } catch (err) {
        // ... (logika za rukovanje greškom ostaje ista) ...
        console.error("DEBUG SERVICE: Login failed:", err.response?.data || err.message);
        
        const errorMessage = err.response?.data?.message || err.message || "Login failed";
        
        dispatch(loginFailure(errorMessage)); 
    }
};


export const handleRegistration = async (registrationData, dispatch, navigate) => {
    
    dispatch(clearAuthError()); 
    // Postavljamo loading state ako imamo Redux loading implementaciju (opcionalno)
    // dispatch(setLoading(true)); 

    try {
        // 1. API poziv za Registraciju (postavlja kolačiće na serveru)
        await registerUser(registrationData);
        
        // 2. dohvatimo user data korisnika sa novim cookies
        // Tvoj API salje sve potrebne podatke (user, battery, solar_system, iot_devices)
        const userDetails = await fetchUserDetails(); 

        console.log("DEBUG SERVICE: Registration success, user details fetched:", userDetails);

        // 3. Azuriranje Redux stanja (KORISTIMO ISTI loginSuccess REDUCER)
        dispatch(loginSuccess(userDetails));

        // 4. Navigacija
        navigate('/');

    } catch (err) {
        // 5. Rukovanje greskom
        console.error("DEBUG SERVICE: Registration failed:", err.response?.data || err.message);
        
        const errorMessage = err.response?.data?.error || err.message || "Registration failed";
        
        // Dispatch Redux akcije za neuspeh
        dispatch(loginFailure(errorMessage)); 
    } 
    // finally { dispatch(setLoading(false)); }
};