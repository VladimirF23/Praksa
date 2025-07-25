
//za redux 

import {configureStore} from '@reduxjs/toolkit';
import authReducer from '../features/authorization/authSlice'; //ovo importuje default default export is AuthSlice-a tj ovo export default authSlice.reducer
// authReducer = authSlice.reducer
/*
reducer je funkcija koja prima trenutno stanje i akciju i vraca novo stanje
- opisuju kako se stanje menja u zavisnosti od akcije
- nikad ne mutatuju state direktno vec returnuju novi copy od state-a
*/

//pravimo redux store i set up-ujemo reducer-a
const store = configureStore({
    reducer: {
        auth: authReducer,          //auth key je slice od state-a  authReducer je nadlezan za taj slice, u globalnom state Tree-u data menagovan od authReducer-a
    },                              //govori Redux-u za auth slice of state koristi authReducer da handlujes promene
    // Ova linija dole je za Redux DevTools
    // koristi browser extensiju ako je dostupna
    // U production buildu, Redux Toolkit automatically disabluje DevTools za mene
    devTools: process.env.NODE_ENV !== 'production',
});

/*u store-u ce ziveti svi state-ovi npr ovako:
{
  auth: {
    isAuthenticated: false,
    user: null
  },
  // other slices can go here
}

*/

export default store;

