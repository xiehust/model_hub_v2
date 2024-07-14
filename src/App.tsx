import React from 'react';
import logo from './logo.svg';
import './App.css';
import {
  BrowserRouter as Router,
  Routes,
  Route,
  useNavigate,
} from "react-router-dom";

import JobTable from './pages/jobs'
import NotFound from './pages/commons/no-found';
import CreateJobApp from './pages/jobs/create-job';
import JobDetailApp from './pages/jobs/job-detail';


function App() {
  return (
    <div className="App">
      <Router>
        <Routes>
          <Route path="/" element={<JobTable/>} />
          <Route path="/jobs" element={<JobTable/>} />
          <Route path="/jobs/createjob" element={<CreateJobApp/>} />
          <Route path="/jobs/:id" element={<JobDetailApp/>} />
          <Route path="*" element={<NotFound/>} />
        </Routes>
      </Router>

    </div>
  );
}

export default App;
