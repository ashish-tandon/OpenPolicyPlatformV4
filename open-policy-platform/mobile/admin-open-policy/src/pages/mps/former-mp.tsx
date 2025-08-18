import { IoSearchOutline } from 'react-icons/io5';
import MPCard, { MPCardProps } from '../../components/MPCard';
import Select from '../../components/common/Select';
import { useEffect, useState } from 'react';
import api from '../../api/axios';
import { Link } from 'react-router-dom';

const provinces = [
  { value: 'all', label: 'All Province' },
  { value: 'on', label: 'Ontario' },
  { value: 'bc', label: 'British Columbia' },
  { value: 'ab', label: 'Alberta' },
];

const FormerMps = () => {
  const [mps, setMps] = useState<MPCardProps[]>([]);
  const [selected, setSelected] = useState('');
  const [provinces, setProvinces] = useState([]);
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');

  const loadBills = async () => {
    try {
      const response = await api.get('/web/former-politician', {
        params: {
          province: selected,
          search: search,
        },
      });

      setProvinces(response.data.provinces);
      setMps(response.data.politicians);

      console.log(response.data);
    } catch (error) {
      // showError(error.response?.data.message || error.message);
    }
  };

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSearch(search);
    }, 300); // 300ms debounce delay

    return () => {
      clearTimeout(handler);
    };
  }, [search]);

  useEffect(() => {
    loadBills();
  }, [selected, debouncedSearch]);
  return (
    <div className="pt-[1rem]">
      <div className="grid md:grid-cols-2 grid-cols-1 gap-4 md:gap-12 padding-x bg-white pb-4">
        <h1 className="text-[32px] md:text-[40px] text-[#222222] font-['SFProDisplay']">
          Former Members of <span className="text-[#AFAFAF]">Parliament</span>
        </h1>
        {/* <p className="text-[#222222] text-[14px] md:mt-0 mt-2">
          Looking for your MP? Enter your postal code in the search field at the
          upper right of the page. Looking for an ex-Member? See our list of
          <Link
            to="/former-mps"
            className="text-[#628ECB] hover:text-[#4A6B99] transition-colors"
          >
            {' '}
            former MPs (since 1994).
          </Link>
        </p> */}
      </div>
      <div className="sticky top-[80px] z-10 bg-white">
        <div className="bg-[#F4F4F4] min-h-[92px] w-full padding-x flex flex-col md:flex-row items-center justify-between py-4 md:py-0 gap-4 md:gap-0">
          <div className="max-w-[628px] w-full bg-white rounded-[24px] h-[44px] border border-[#EDEDED] flex items-center justify-between">
            <div className="flex items-center gap-3 w-full px-4">
              <img src="/assets/images/logo2.svg" alt="" className="w-6 h-6" />
              <input
                type="text"
                placeholder="Search Members"
                className="placeholder:text-[#D3D3D3] w-full outline-none border-none"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <IoSearchOutline className="mr-4 cursor-pointer" size={20} />
          </div>

          <div className="flex items-center gap-3 flex-wrap justify-center md:justify-end w-full md:w-auto">
            {/* <Select
              options={provinces}
              placeholder="All Province"
              width="w-full md:w-[200px]"
              onChange={(value) => setSelected(value)}
            /> */}
          </div>
        </div>
      </div>
      <div className="padding-x mt-8 space-y-6">
        {mps.map((mp, index) => (
          <MPCard key={index} {...mp} />
        ))}
      </div>
    </div>
  );
};

export default FormerMps;
