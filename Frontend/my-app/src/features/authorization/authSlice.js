
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
        loginSuccess: (state, action) => {
            const { user, battery, solar_system, iot_devices } = action.payload;

            state.isAuthenticated = true;
            state.user = user;
            state.battery = battery || null;
            state.solarSystem = solar_system || null;

            // Corrected logic to handle both payload structures, i za /me  i za livemetering
            if (Array.isArray(iot_devices)) {
                state.iotDevices = iot_devices;
            } else if (iot_devices && iot_devices.devices && Array.isArray(iot_devices.devices)) {
                state.iotDevices = iot_devices.devices;
            } else {
                state.iotDevices = [];
            }

            state.error = null;
        },
        logout:(state) =>{
            state.isAuthenticated = false;
            state.user = null;
            state.battery = null;
            state.solarSystem = null;
            state.iotDevices = [];
            state.error = null;
            state.loading = false;
        },
        //kako radi Redux Toolkit kada se pozove loginFailure(errorMessage) i prosledi erroMessage, toolkit napravi action objekat koji ovako izgleda
        //{type: 'auth/loginFailure' payload errorMessage}
        // prvi parametar state se odnosi na slice (auth o ovom sluc) a drugi je action object koji sadrzi type i payload tj errormessage
        loginFailure: (state,action) =>{
            state.isAuthenticated=false;
            state.user= null;
            state.battery = null;
            state.solarSystem = null;
            state.iotDevices = [];
            state.error = action.payload;
            state.loading = false;

        },

         // novi reducer za when backend sends a fresh list (after /me fetch, or via socket when automation kicked in).
        setIotDevices: (state, action) => {
            state.iotDevices = action.payload || [];
        },
        toggleIotDevice: (state, action) => {                               //a ovo je kada user manuelno interektuje sa IoT (clikne na UI)
            const { deviceId, status } = action.payload;
            state.iotDevices = state.iotDevices.map((d) =>
                d.device_id === deviceId ? { ...d, current_status: status } : d
            );
        },
        // --- NEW REDUCER FOR PRIORITY UPDATE ---
        updateIotDevicePriorityRedux: (state, action) => {
            const { deviceId, priority } = action.payload;
            state.iotDevices = state.iotDevices.map((d) =>
                d.device_id === deviceId ? { ...d, priority_level: priority } : d
            );
        },


        // MISLIM DA setUserDetails nigde ne koristim i da ne treba

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
export const { loginSuccess, loginFailure, logout, setUserDetails, clearAuthError,setLoading,authCheckStart,authCheckComplete,setIotDevices ,toggleIotDevice,updateIotDevicePriorityRedux } = authSlice.actions;       
export default authSlice.reducer;                           // funkcija koju Redux zove da updejtuje state