import React from 'react';
import { IconType } from 'react-icons';

interface EmptyStateProps {
  icon?: IconType;
  message: string;
  description?: string;
  className?: string;
}

const EmptyState: React.FC<EmptyStateProps> = ({
  icon: Icon,
  message,
  description,
  className = '',
}) => {
  return (
    <div
      className={`flex flex-col items-center justify-center p-8 ${className}`}
    >
      {Icon && (
        <div className="mb-4">
          <Icon className="w-20 h-20 text-gray-400" />
        </div>
      )}
      <h3 className="text-lg font-medium text-gray-900 mb-2">{message}</h3>
      {description && (
        <p className="text-lg text-gray-500 text-center max-w-sm">
          {description}
        </p>
      )}
    </div>
  );
};

export default EmptyState;
