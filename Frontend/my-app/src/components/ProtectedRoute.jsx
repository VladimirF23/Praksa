
// /ProtectedRoute.jsx
import React from "react";
import { useSelector } from "react-redux";
import { Navigate, Outlet } from "react-router-dom";

const ProtectedRoute = ({children,adminOnly = false}) =>{
    const isAuthenticated  = useSelector((state) => state.auth.isAuthenticated);        //iz redux-a
    const user = useSelector((state) => state.auth.user);

    // loading state je vazan za handlovanje incijalnog app load-ovanja,
    // kada Redux state nije jos azuran ili  autentifikacija  idalje traje onda 

    
    const isLoading = useSelector((state) => state.auth.loading); // treba dodati loading state

    //1. Handlovanje loading state-a
    // ako se authentification status ceka (npr pri pokretanju app-a ili pri proveri validnosti prilikom refresh-a) pokazuje se loading indicator
    // to sprecava flicker ka loading page-u pre nego sto app zna userov status


    // VAZNO Ne renderujemo nista dok je provera autentifikacije u toku
    // Ovo sprečava renderovanje zasticenog sadržaja (ili preusmeravanje) 
    // dok se inicijalna provera autentifikacije ne zavrsi
    //  To eliminise treperenje UI-a i sprecava da se neautorizovani API pozivi pokrenu prerano 
    if(isLoading){
        return null;
    }

    //2. Handlovanje neprijavljenih user-a
    // ako nije prijavljen user ne moze da pristupa protected content-u i redirectujemo ga ka login page-u
    if (!isAuthenticated){
        // replace prop osigura da login page zameni trenutan entry u history stack
        // Ovo sprecava user-a da da se vrati nazad do protected page-a direktno koristeci web browser-ov back dugme
        return <Navigate to="/login" replace />;

    }

    //3. Handlovanje Unauthorized (non Global Admini) za Global-Admin-Only Routes
    // ovo provera se koristi ako je `adminOnly` prop je pass-ovan kao true ka ProtectedRoute.
    // Proverava da li autentifikovani user ima  'global_admin' privilegiju
    if (adminOnly && (!user || !user.global_admin)) {
        // Ako je prijavljen i nije global admin redirectujemo ga /403 page-u
        //koristimo replace iz istih history management razloga
        return <Navigate to="/403" replace />;      //ovo je AccesDeniedPage.jsx
    }


    // 4. Renderovanje zasticenog Content-a
    // Ako sve provere prodje (user je privaljen i ima required role ako je 'adminOnly'  true)
    // onda renderujemo content od rout-a
    // 'children' se koristi ako pass-ujemo direct JSX kao child od ProtectedRoute.
    // 'Outlet' se koristi kada nest-ujemo routes unutar <Route element={<ProtectedRoute />} /> u mom App.js.
    return children ? children : <Outlet />;

    //primer ovoga:
    //When you define a route like
    //  <Route path="/dashboard" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>}>, 
    // the DashboardPage component becomes the children prop of ProtectedRoute.

    //When you define nested routes using an element prop like
    // <Route element={<ProtectedRoute />}><Route path="/dashboard" element={<DashboardPage />} /></Route>, 
    // the DashboardPage component is rendered by the <Outlet /> component within ProtectedRoute. 
    // This is generally the more common and flexible way to use ProtectedRoute for multiple nested protected routes.

};

export default ProtectedRoute;