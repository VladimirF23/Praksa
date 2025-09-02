//login forma, handluje submisiion od user-a, dispatchuje login action i menaguje error-e
//updejtuje redux store

import React, {useState} from "react";
import { useDispatch, useSelector } from "react-redux";
import { loginUser } from "../api/authApi";

//Reduceri za redux store state
import { loginSuccess,loginFailure,clearAuthError} from "../features/authorization/authSlice";
import axiosInstance from "../api/axiosInstance";
import { useNavigate } from 'react-router-dom'; 






const Login = () =>{
    const [username,setUsername] = useState('');
    const [password,setPassword] =  useState('');

    //pristupimo error-u preko Redux state-a
    /*
        const initialState = {
            isAuthenticated: false,
            user: null,
            error:null
        };

        ovaj state definise authSlice i on ga modifikuje
    */
    const error = useSelector((state) => state.auth.error)
    
    //inicijalizujemo redux dispatch
    const dispatch = useDispatch()
    const navigate = useNavigate(); // inicijalizujemo navigate hook, ako se uspesno loginuje dole ga pomerimo na homepage


    //handlujemo submit logina
    const handleSubmit = async(e) =>{
        e.preventDefault();                 //preventujemo page reload
        dispatch(clearAuthError());         //ocistimo prethodne error-e
        try{
            const credentials = {username,password};

            //calujemo login AXIOS-a koji salje API-u, Ovo ce set-ovati HTTPOnly cookies 
            await loginUser(credentials)
            const userDetailsResponse = await axiosInstance.get('/api/auth/me');                    // novi API call treba samo da dodam   
            const userDetails = userDetailsResponse.data;

            console.log("DEBUG POSLE USPESNOG LOGIN-a: userDetails before dispatch", userDetails);

            dispatch(loginSuccess(userDetails));                                                    // Dispatch-ujemo ka Redux-u sa podacima od user-a
            navigate('/');                                                                          // Na home page ga redirectujemo



            //Ne treba mi local storage jer Browser menagaguje HttpOnly cookie 
            //localStorage.setItem('token',data.access_token)   
            
        }catch(err){

            //mi dispatchujemo ovo, redux salje action ka reducer-u loginFailiure (AuthSlice), reducer kalkulise nove stanje i akciju, store save-uje novo stanje
            //UI componente slusaju store i updejtuju sami sebe na osnovu novog state-a
            const errorMessage = err.response?.data?.message || err.message || "Login failed";
            
            //treba samo 1 parametar objasnio sam u authSlice-u sto
            dispatch(loginFailure(errorMessage));
        }
    };



return (
  <div 
    style={{
      display: "flex",
      justifyContent: "center",
      alignItems: "center",
      minHeight: "100vh",
      backgroundColor: "#f3f4f6"
    }}
  >
    <form 
      onSubmit={handleSubmit}
      style={{
        background: "#fff",
        padding: "2rem",
        borderRadius: "12px",
        boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
        width: "100%",
        maxWidth: "400px"
      }}
    >
      <h2 style={{ textAlign: "center", marginBottom: "1.5rem" }}>Login</h2>

      <div style={{ marginBottom: "1rem" }}>
        <label style={{ display: "block", marginBottom: ".5rem", fontWeight: "500" }}>
          Username
        </label>
        <input
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          style={{
            width: "100%",
            padding: ".75rem",
            borderRadius: "8px",
            border: "1px solid #ccc",
            outline: "none"
          }}
          placeholder="Enter your username"
        />
      </div>

      <div style={{ marginBottom: "1rem" }}>
        <label style={{ display: "block", marginBottom: ".5rem", fontWeight: "500" }}>
          Password
        </label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          style={{
            width: "100%",
            padding: ".75rem",
            borderRadius: "8px",
            border: "1px solid #ccc",
            outline: "none"
          }}
          placeholder="••••••••"
        />
      </div>

      <button
        type="submit"
        style={{
          width: "100%",
          padding: ".85rem",
          background: "#2563eb",
          color: "#fff",
          fontWeight: "600",
          border: "none",
          borderRadius: "8px",
          cursor: "pointer",
          transition: "background .3s ease"
        }}
        onMouseOver={(e) => (e.target.style.background = "#1e40af")}
        onMouseOut={(e) => (e.target.style.background = "#2563eb")}
      >
        Login
      </button>

      {error && (
        <p style={{ color: "red", marginTop: "1rem", textAlign: "center" }}>
          {error}
        </p>
      )}
    </form>
  </div>
);

};
export default Login;
