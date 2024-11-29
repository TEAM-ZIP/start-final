import axios from "axios";

const baseURL = "http://43.201.210.211:8080";
const instance = axios.create({
  baseURL: baseURL,
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
});

export default instance;
