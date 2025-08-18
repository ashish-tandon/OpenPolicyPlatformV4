import React from 'react';
import { useLocation, useParams } from 'react-router-dom';

function VoteSearch() {
  const location = useLocation();
  const fullPath = location.pathname.replace('/votes/', ''); // "44-1/927"
  return <div>Not Available</div>;
}

export default VoteSearch;
