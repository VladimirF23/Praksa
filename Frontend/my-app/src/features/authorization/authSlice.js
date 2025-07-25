
// authSlice.js

import { createSlice } from "@reduxjs/toolkit";

//inicijalno stanje za auth slice, user cuva user data
const initialState = {
    isAuthenticated: false,
    user: null,
    error:null,
    loading: true       //inicijalni state za loading kada se startuje app an user-ovom browseru

};

// Loading je bitan jer user se loguje na app i zatvori browser i dodje 1h kasnije, JWT access i refresh se storuju u HTTPonly cookies i oni ostaju
// u browser sessionu dok ne isteknu ako ne proverimo load user ce biti logoutovan a ako pokusaju da pristupe protected routu oni ce biti redirectovani ka
// loginu/registeru iako oni imaju validne sesije (los user exp)

//  startovanj app-a -> startovanje kod user-a skida JS bundle, parsira i executuje code,inicijal React componente, inicijalni data fetch i authenfication check-ovi
//  Loadovanje       -> period kada app aktivno pokusava da odredi authentification state od user-a -> a)pravljenje /api/auth/me API request-a
//                                                                                                     b) cekanje odgovora od servera, updetovanje Redux-a

//loadovanje i startovanje su slicni...

//authSlice definise kako state izgleda i kako se moze updejtovati, inicijalizujemo initialState, reduceri ->modifikuju state
const authSlice = createSlice({
    name:'auth',
    initialState,
    reducers: {
        loginSuccess:(state,action) =>{
            state.isAuthenticated = true;
            state.user = action.payload;        // Flask nece vracati podatke o user-u preko login-a trebace mi odvojen API request get da dobijem info o user-u  
            state.error= null;
            state.loading = false;
        },
        logout:(state) =>{
            state.isAuthenticated = false;
            state.user = null;
            state.error=null;
            state.loading = false;
        },
        //kako radi Redux Toolkit kada se pozove loginFailure(errorMessage) i prosledi erroMessage, toolkit napravi action objekat koji ovako izgleda
        //{type: 'auth/loginFailure' payload errorMessage}
        // prvi parametar state se odnosi na slice (auth o ovom sluc) a drugi je action object koji sadrzi type i payload tj errormessage
        loginFailure: (state,action) =>{
            state.isAuthenticated=false;
            state.user= null;
            state.error = action.payload;
            state.loading = false;

        },
        //reducer za podesavanja user info-a nakon uspesnog login-a / refresh-a
        //Ovako mora zato sto su JWTs su HttpOnly, Treba da dobijemo user data iz odvojenog point-a
        setUserDetails: (state, action) => {
            state.user = action.payload;
            state.loading = false;
        },
        //za ciscenje prethodnih login error-a, korisno kad user se ponovo login-unuje
        clearAuthError: (state) => {
            state.error = null;
        },

        // --- Reduceri za LOADING STATE ----

        setLoading: (state, action) => {
            state.loading = action.payload; // Dozvoljava postavljanje loading da bude true ili false
        },
        // Action koji oznacava da auth check pocinje (e.g., na app load-u)
        authCheckStart: (state) => {
            state.loading = true;
            state.error = null; // cistimo prethodne error-e kada novi check krene
        },
        // Action koji oznacava da se auth check zavrsio (success or failure handlujemo drugde)
        authCheckComplete: (state) => {
            state.loading = false;
        }


    },
});

//exportuje action creator-s (loginSuccess... i loggout) za koriscenje u components da bi se discpatch-ovale ove akcije
export const { loginSuccess, loginFailure, logout, setUserDetails, clearAuthError,setLoading,authCheckStart,authCheckComplete } = authSlice.actions;       
export default authSlice.reducer;                           // funkcija koju Redux zove da updejtuje state