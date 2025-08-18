import React from 'react';
import { useLocation, useParams } from 'react-router-dom';

function CommitteeSearch() {
  const location = useLocation();
  const fullPath = location.pathname.replace('/committees/', '');
  return <div>{fullPath}</div>;
}

export default CommitteeSearch;
