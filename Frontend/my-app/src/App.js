// App.js
import React, {useEffect, useRef} from 'react';
import { Provider,useDispatch,useSelector } from 'react-redux';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import store from './app/store';

import Navbar from "./components/Navbar";
import Home from "./pages/Home";
import Login from "./pages/Login";
import Register from "./pages/Register";
import ProtectedRoute  from "./components/ProtectedRoute";
import NotFoundPage from "./pages/NotFoundPage"; 
import AccessDeniedPage from './pages/AccessDeniedPage';

//za redus stanje
import { authCheckStart,loginSuccess,authCheckComplete } from './features/authorization/authSlice';
//API
import axiosInstance from './api/axiosInstance';
 


/*
React Router biblioteka koja omogucava routing u React app-u, dozvoljava app-u da prikaze razl pages (Home,Register,Login,Subreddit,post) preko URL u browser-u
handluje navigaciju i renderovanje komponenata tako da se ne primeti ->npm install react-router-dom

BrowserRouter as Router:
  -main routing component koja enabluje routing u mom app-u. Gleda promene URL-a i renderuje na odgovarajuce components
Route:
  -Definise individualne routes koji mapiraju specificne path-ove (/login,/register) na odgovarajuci React Component
Routes:
  - Wraper za group-ovanje vise <Route> components

Ja importujemo moje page components(Home,Login..) from pages Directory


*/

/*Svaki <Route> component definise path i component da renderuje
  Kada URL path match-uje '/' renderovace <Home> component, element= nam govori koju komponentu treba renderovati

  Dynamic Routes:
  :subreddit i :postId su route parameters, Oni su placeholderi za dynamic values u URL-u
  Primer:
    Ako posetim /r/javascript , <Subreddit/> component se renderuje i subreddit ce biti "javascript"
    Ako posetim /r/javascript/123, <Post> component se renderuje sa subreddit="javascript" i postId =123


    Mogu da pristupim ovim parametrima unutar componenta koristeci useParams hook ovako
    import { useParams } from "react-router-dom";

  const Subreddit = () => {
    const { subreddit } = useParams();
    return <h1>Welcome to {subreddit} subreddit!</h1>;
}

*/


// primereri dummy component-a za protektovane page-ove
const Dashboard = () => <h2>Welcome to your Dashboard! (Protected)</h2>;
const AdminPage = () => <h2>Welcome, Admin! (Admin Only)</h2>;


const AppContent  = () => {
  const dispatch = useDispatch();


// Uzmi loading stanje iz Reduxa
const isLoading = useSelector((state) => state.auth.loading); 
const hasAuthCheckRun = useRef(false);

// kad se pokrene app na user-ovom browser-u ovo se pokrece
useEffect(() => {

  if (hasAuthCheckRun.current) {
                                        
            return;                                                                               // Ako je check vec pokrenut, ne radimo nista
  }
  hasAuthCheckRun.current = true;                                                                 // Flag-ujemo da check je sada pokrenut

  const checkAuthStatus = async () => {
    console.log("DEBUG: Auth check started.");
    dispatch(authCheckStart());                                                                   // Stavljamo loading na true, clear error-e



    try {
      console.log("DEBUG: Attempting to get user details from /api/auth/me");


      const userDetailsResponse = await axiosInstance.get('/api/auth/me');


      console.log("DEBUG: User details response received:", userDetailsResponse.data);
      const userDetails = userDetailsResponse.data;
      dispatch(loginSuccess(userDetails));                                                         // User je autenfitikovan, postavljamo details
      console.log("DEBUG AppContent: User authenticated successfully.");

    } catch (error) {
      console.error("DEBUG: Initial /api/auth/me request failed. Error details:", error.response?.data || error.message);
      //  axios interceptor handluje logout/redirect ako refresh fail-uje
      // Ne treba da dispatchujem logout() ili redirect ovde  direktno
      console.log("Initial auth check failed or refresh failed. User is not authenticated. Interceptor handled.");

    } finally {
      console.log("DEBUG: Auth check complete (finally block).");
      dispatch(authCheckComplete());                                                            // Stavljamo loading na false za svaki outcome
    }
  };
  checkAuthStatus();
}, [dispatch]);

  // Dodao uslovno renderovanje dok se ne zavrsi provera autentifikacije
  // ovo je vazno
    if (isLoading) {
        return <div>Loading application...</div>; //mogu da stavim ovde spinner neki
    }

  return( 
  <Router>
    <Navbar/>   {/*Da uvek bude vidljiv */}
    <Routes>
      <Route path="/" element={<Home />} />          
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/403" element={<AccessDeniedPage />} /> {/* novi 403 page */}


      {/*Public Routes sa Dimamickim Parametrima */}



      {/* --- Protected Routes --- */}
      {/* Bilo koji route nestovan ovde ce zahtevati autentifikaciju */}
      <Route element={<ProtectedRoute />}>
      <Route path="/dashboard" element={<Dashboard />} />
      {/* Add more protected routes here */}
       {/* Primer: <Route path="/live-board" element={<CheckLiveBoard />} /> 
                   <Route path ="/myProfile" ..../>
       */}
      </Route>

      {/* --- Admin-only Protected Route --- */}
      {/* Ova route zahteva oba authentication I admin privileges */}
      <Route element={<ProtectedRoute adminOnly={true} />}>
          <Route path="/admin" element={<AdminPage />} />
      </Route>

      {/* Optional: Add a 404 Not Found page */}
      <Route path="*" element={<NotFoundPage />} />




    </Routes>
  </Router>
  );
};


//  main App component sada wrapuje AppContent sa Redux Provider, sto dozvoljava da sve komponente App-a mogu da vide Provider Store tj redux 
//  i tu npr osim sto smo stavili podatke od trenutno ulogovanog korisnika treba da stavimo IoT,SolarSystem,user podatke
// ovo se radi da bi imali centralizovan pristup tim podacima i da ne bi smo morali da spamujemo useState tj drill propujemo
// mada nije preporucljivo da se ovako radi u velikim aplikacijama posto ako bi se promenio novi post morali bi svi postovi opet da se renderuju
const App = () => (
    <Provider store={store}>
        <AppContent />
    </Provider>
);
export default App;   //da bi App component dostupan za korisceneni u drugim partovima aplikacije  
