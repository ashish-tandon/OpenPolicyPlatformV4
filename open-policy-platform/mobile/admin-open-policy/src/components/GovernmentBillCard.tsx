import { FC } from 'react';
import { useNavigate } from 'react-router-dom';

export interface GovernmentBillCardProps {
  id: string | number;
  billNumber: string;
  title: string;
  status: 'Failed' | 'Law' | 'Passed' | '';
  date?: string;
  subtitle?: string;
}

const GovernmentBillCard: FC<GovernmentBillCardProps> = ({
  id,
  billNumber,
  title,
  status,
  date,
  subtitle,
}) => {
  const navigate = useNavigate();

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Failed':
        return 'text-[#DD3434]';
      case 'Law':
        return 'text-[#628ECB]';
      case 'Passed':
        return 'text-[#4F8C10]';
      default:
        return '';
    }
  };

  return (
    <div
      onClick={() => navigate(`/bills/${id}`)}
      className="p-4 rounded-[24px] shadow-md hover:shadow-lg transition-all cursor-pointer h-[240px] max-w-[411px] min-w-full w-full"
    >
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-3">
          <span className="bg-[#F3F3F3] w-[99px] h-[44px] rounded-full text-[#395886] font-['SFProTextMedium'] flex items-center justify-center">
            {billNumber}
          </span>
          <span className={`font-['SFProTextBold'] ${getStatusColor(status)}`}>
            {status}
          </span>
        </div>
        {date && (
          <span className="text-[#B4B4B4] text-[12px] font-['SFProTextSemiBold'] italic">
            {date}
          </span>
        )}
      </div>

      <h3 className="text-lg font-['SFProTextMedium'] text-[#222222] mb-1">
        {title}
      </h3>

      {subtitle && (
        <p className="text-[12px] text-[#B4B4B4] font-['SFProTextSemiBold']">
          {subtitle}
        </p>
      )}
    </div>
  );
};

export default GovernmentBillCard;
