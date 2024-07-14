// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import axios from 'axios';
console.log(process.env)
export const API_ENDPOINT= process.env.REACT_APP_API_ENDPOINT;
export const API_KEY = process.env.REACT_APP_API_KEY;

export const remotePost = async(formdata,path) =>{
    console.log('api:',`${API_ENDPOINT}/${path}`)
    const headers = {'Content-Type': 'application/json', 
        'Authorization': `Bearer ${API_KEY}`
        };
    try {
        const resp = await axios.post(`${API_ENDPOINT}/${path}`,JSON.stringify(formdata), {headers});
        if (resp.statusText === 'OK'){
            return resp.data
        } else{
            console.log(`Server error:${resp.status}`)
            throw `Server error:${resp.status}`;
        }

    } catch (err) {
        throw err;
    }
}