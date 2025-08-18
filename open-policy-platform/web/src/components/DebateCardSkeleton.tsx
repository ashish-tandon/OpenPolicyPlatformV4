import React from 'react';

const DebateCardSkeleton: React.FC = () => {
  return (
    <>
      <style>{`
        .skeleton {
          position: relative;
          overflow: hidden;
          background-color: #e5e7eb; /* Tailwind gray-200 */
        }

        .skeleton::after {
          content: '';
          position: absolute;
          top: 0;
          left: -100%;
          height: 100%;
          width: 100%;
          background: linear-gradient(
            90deg,
            transparent,
            rgba(255, 255, 255, 0.6),
            transparent
          );
          animation: shimmer 1.6s infinite;
        }

        @keyframes shimmer {
          100% {
            left: 100%;
          }
        }
      `}</style>

      <div className="flex flex-col md:flex-row gap-4 md:gap-6 p-4 md:p-6 rounded-2xl w-full shadow-sm bg-white border border-gray-100">
        {/* Left panel */}
        <div className="flex flex-col items-start md:items-end min-w-0 md:min-w-[200px] w-full md:w-auto space-y-2">
          <div className="skeleton h-4 w-full rounded-md" />
          <div className="skeleton h-3 w-1/2 rounded-md" />
          <div className="skeleton h-3 w-3/4 rounded-md" />
          <div className="skeleton h-3 w-2/3 rounded-md" />
          <div className="skeleton h-4 w-1/3 rounded-md" />
        </div>

        {/* Right panel */}
        <div className="flex flex-col md:flex-row gap-4 w-full items-start">
          <div className="skeleton rounded-full w-[80px] h-[80px] md:w-[120px] md:h-[120px]" />
          <div className="flex flex-col flex-grow space-y-3 w-full">
            <div className="flex items-center gap-3">
              <div className="skeleton h-4 w-1/3 rounded-md" />
              <div className="skeleton h-3 w-1/4 rounded-md" />
            </div>
            <div className="space-y-2">
              <div className="skeleton h-3 w-full rounded-md" />
              <div className="skeleton h-3 w-11/12 rounded-md" />
              <div className="skeleton h-3 w-5/6 rounded-md" />
              <div className="skeleton h-3 w-1/2 rounded-md" />
            </div>
            <div className="skeleton h-3 w-1/6 rounded-md" />
          </div>
        </div>
      </div>
    </>
  );
};

export default DebateCardSkeleton;
