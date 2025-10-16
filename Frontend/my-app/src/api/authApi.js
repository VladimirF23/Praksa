
// src/api/authApi.js
import axios from "axios";
import axiosInstance  from "./axiosInstance";
import AuthError  from "../utils/AuthError";
import Cookies from 'js-cookie';


// Kreirana POSEBNA Axios instancu samo za refresh token pozive
const refreshAxiosInstance = axios.create({
    baseURL: 'https://solartrack.local', 
    headers: {
        'Content-Type': 'application/json',
    },
    withCredentials: true,
    // *** KLJUCNA IZMENA: Eksplicitno definisemo validateStatus ***
    // Ovo osigurava da Axios uvek odbije Promise za 4xx/5xx statuse
    validateStatus: function (status) {
        return status >= 200 && status < 300; // Odbij ako status nije 2xx
    },
});

// *** KLJUCNO:  request interceptor za refreshAxiosInstance ***
refreshAxiosInstance.interceptors.request.use(
    (config) => {
        // Procitaj CSRF token za refresh iz csrf_refresh_token cookie-a
        const csrf_refresh_token = Cookies.get('csrf_refresh_token');

        // Ako postoji refresh CSRF token, dodaj ga u header
        if (csrf_refresh_token) {
            config.headers['X-CSRF-TOKEN'] = csrf_refresh_token; 
            console.log("DEBUG AUTHAPI: Adding X-CSRF-TOKEN (refresh) to refresh request."); // Dodato za debug
        } else {
            console.warn("DEBUG AUTHAPI: csrf_refresh_token cookie not found for refresh request."); // Upozorenje ako nedostaje
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);


//ova funkcija ce zvati API login-e
export const loginUser = async(credentials) =>{
    try{
        //post request, preko axiosa nginx ce proslediti na moj pravi API, api ovde je za nginx i on ce skinuti /api/ 
        const response = await axiosInstance.post('/api/auth/login',credentials);

        return response.data        // Flask vraca {"message": "User logged in successfully"}
    }catch(error){
        //catchujem error posto mi API vraca error a ne message
        
        if (error.response && error.response.data && error.response.data.error) {
            throw error.response.data.error;
        }else{
            throw new Error("An unexpected error occurred.");
        }
    }
};

export const logoutUser = async() =>{
    try{
        const response = await axiosInstance.post('/api/auth/logout');
        return response.data;
    }catch(error){
        console.error("DEBUG authApi: logoutUser failed:", error.response?.data || error.message);
        throw error; //  Ovo osigurava da interceptor's catch blok uhvati gresku

    }

};

// Ovo zove preko NOVOG AXIO-sa refreshAxiosInstance /refresh koristim novi AXIOS posto ovaj nema responce interceptor-a
//zakacenog i da onda ne bi doslo DO BESKONACNE PETLJE kada bi refresh fail-ovao jer da ima responce interceptor onda bi on ponovo pokusao da se refresh-uje -> besk petlja
// kada ovaj refreshToken propadne on ce baciti AuthError koji cemo mi uhvatiti u try catch block-u interceptora koji je bio pozvan za request koji je zvao
// refresh !!
export const refreshToken = async() =>{

    console.log("DEBUG AUTHAPI: Trying to refresh token. Using refreshAxiosInstance."); // Dodato logovanje

    try{
        // Flask-ov /auth/refresh je POST request treba mu validan refresh token cookie
        // i trebace mu validan CSRF token iz JS readable cookie-a

        console.log("DEBUG AUTHAPI: Sending POST to /api/auth/refresh..."); // Dodato logovanje


        //preko refresh AxiosInstance-a posto on nema prikljucene interceptore
        const response = await refreshAxiosInstance.post('/api/auth/refresh',{},{withCredentials:true});


        console.log("DEBUG AUTHAPI: Successfully received refresh response:", response.data); // Dodato logovanje

        return response.data;       //dobicemo samo poruku da su postavljeni novi cookie

    }catch(error)
    {
        // refresh je fail-ovao sto znaci da je istekao access cookie ili je user banovan i onda ce se tamo u responce interceptoru uhvatiti ovaj exception
        // i forsiracese login da se ponovi
        console.error("DEBUG AUTHAPI: refreshToken caught Axios error:", error.response?.data || error.message || error); 
        console.error("DEBUG AUTHAPI: Full error object details from refreshAxiosInstance:", error); 
        throw new AuthError("Failed to refresh token", error.response?.status || 0); 
    
    }

};
export const fetchUserDetails = async () => {
    try {
        // Koristimo axiosInstance (onaj koji ima interceptore za refresh)
        const response = await axiosInstance.get('/api/auth/me'); 
        return response.data; // Vraca podatke o korisniku
    } catch (error) {
        console.error("DEBUG authApi: fetchUserDetails failed:", error.response?.data || error.message);
        throw error; // Propagiraj grešku
    }
};


export const registerUser = async (registrationData) => {
    try {
        //  backend endpoint je: /registration
        const response = await axiosInstance.post('/api/registration', registrationData);
        // Ne vraća korisnika, već postavlja kolačiće.
        return response.data; 
    } catch (error) {
        console.error("DEBUG authApi: registerUser failed:", error.response?.data || error.message);
        // Baci gresku nazad u servisni sloj
        throw error;
    }
};