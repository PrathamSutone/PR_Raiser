import React, { useState, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import './Clone.css';
import Navbar from './Navbar';
import SearchContext from './context/SearchContext';
import LoadingRing from './Loader/Loader';

const Clone = () => {
  const { isLoading, setIsLoading } = useContext(SearchContext);
  const [branches, setBranches] = useState([]);
  const [input, setInput] = useState('');
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);

  const handleClone = async (branch) => {
    setIsLoading(true);
    try {
      const response = await fetch(`/api/clone?path=${input}`);
      const data = await response.json();
      console.log(data);
      setBranches(data);
    } catch (error) {
      console.error(error);
    }
    setIsLoading(false);
  };

  const handleInputChange = (event) => {
    setInput(event.target.value);
  };

  const handleselect = async(branch) => {
    try {
      console.log(branch);
      fetch(`/api/setBranch?path=${input}&branch=${branch}`);
      navigate(`/repos`);
    }
    catch (error) {
      console.error(error);
    }
  };


  return (
    <div>
      <Navbar />
      {isLoading ? (
        <LoadingRing />
      ) : (
        <div>
          <div className="GetIgnorecontainer">
            <label className="pathsearchrow">
              <div className="pathsearchlabel">Clone Repo :</div>
              <input
                type="text"
                value={input}
                onChange={handleInputChange}
                className="pathsearchbar"
              />
            </label>
            <div className="gitIgnorebuttoncontainer">
              {branches.length > 0 ? (
                <div className="dropdown" onMouseLeave={() => setIsOpen(false)}>
                  <button className="userProfileButton" onMouseEnter={() => setIsOpen(true)}>
                    Select Branch :
                  </button>
                  {isOpen && (
                    <ul className="drop-down-list">
                      {branches.map((branch,) => (
                        <li key = {branch}>
                          <button onClick={() => handleselect(branch)}>{branch}</button>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              ) : (
                <button onClick={handleClone} className="gitIgnorebutton">
                  Clone Repository
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Clone;
