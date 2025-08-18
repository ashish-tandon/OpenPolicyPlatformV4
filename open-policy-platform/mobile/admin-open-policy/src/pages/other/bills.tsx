import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation, useParams } from 'react-router-dom';
import api from '../../api/axios';

function BillSearch() {
  const location = useLocation();
  const fullPath = location.pathname.replace('/bills/', '');

  const navigate = useNavigate();

  const loadHouseMentions = async () => {
    try {
      const response = await api.get('/web/get-bill/', {
        params: {
          bill: fullPath,
        },
      });
      navigate(`/bills/${response.data.id}`, { replace: true });

      // setHouseMentions(response.data);
    } catch (error) {
      // showError(error.response?.data.message || error.message);
    }
  };

  useEffect(() => {
    loadHouseMentions();
  }, []);

  return (
    <div className="pt-[2rem] padding-x">
      <div>
        <h1 className="text-[20px] md:text-[24px] font-[SFProTextBold] mt-12 md:mt-20 mb-6 md:mb-8">
          Redirecting
        </h1>
      </div>
    </div>
  );
}

export default BillSearch;
