import React, { useState, useEffect } from 'react';

function CheckAIIgnore({ path }) {
  const [ignoreExists, setIgnoreExists] = useState(null);

  useEffect(() => {
    fetch(`/api/CheckAIIgnore?path=${encodeURIComponent(path)}`)
      .then(response => response.json())
      .then(data => setIgnoreExists(data.AIIgnore))
      .catch(error => console.error(error));
  }, [path]);

  if (ignoreExists === null) {
    return <div>⏳Checking if '.AIIgnore' file exists...</div>;
  } else if (ignoreExists) {
    return <div> AIIgnore file exists ✅</div>;
  } else {
    return <div>Info ⚠️: AIIgnore file does not exist</div>;
  }
}

export default CheckAIIgnore;
