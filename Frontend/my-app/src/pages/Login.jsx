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
        // postojeci JSX za login formu
        <form onSubmit={handleSubmit}>
            <div>
                <label>Username:</label>
                <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                />
            </div>
            <div>
                <label>Password:</label>
                <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                />
            </div>
            <button type="submit">Login</button>
            {error && <p style={{ color: 'red' }}>Error: {error}</p>}
        </form>
    );

};
export default Login;
