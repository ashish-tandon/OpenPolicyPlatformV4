import parse, { domToReact } from 'html-react-parser';
import { Link } from 'react-router-dom';

const getActivityStyle = (type: string) => {
  if (type.includes('Voted No')) return 'text-[#DD3434]';
  if (type.includes('Voted Yes')) return 'text-[#4F8C10]';
  if (type.includes('in the House')) return 'text-[#D9B88E]';
  if (type.includes('committee')) return 'text-[#A4DED2]';
  if (type.includes('legislation')) return 'text-[#E2B8E8]';
};

const options = {
  replace: (domNode: import('html-react-parser').DOMNode) => {
    if (domNode.type === 'tag' && domNode.name === 'a') {
      const { href } = domNode.attribs || {};
      if (href && href.startsWith('/')) {
        return (
          <Link
            to={href}
            className="text-[#628ECB] hover:text-[#4A6B99] transition-colors"
          >
            {domToReact(
              domNode.children as import('html-react-parser').DOMNode[],
              options,
            )}
          </Link>
        );
      }
    }
  },
};

export interface MPCardProps {
  id: string;
  province_name: string;
  politician_image: string;
  name: string;
  election_summary: string;
  role: string;
  activity: {
    isTitle: boolean;
    subtitle: string;
    text: string;
    title: string;
  }[];
  recent_activities: {
    isTitle: boolean;
    subtitle: string;
    text: string;
    title: string;
  }[];
}

const MPCard: React.FC<MPCardProps> = ({
  id,
  province_name,
  politician_image,
  name,
  election_summary,
  role,
  activity,
  recent_activities,
}) => {
  const nameSlug = name.toLowerCase().replace(/\s+/g, '-');

  return (
    <div className="flex flex-col md:flex-row gap-4 md:gap-6 p-4 md:p-6 rounded-[24px] shadow-md">
      <img
        src={politician_image || 'https://fakeimg.pl/600x400/ffffff/fffcfc'}
        alt={name}
        className="w-[120px] h-[120px] md:w-[152px] md:h-[152px] object-contain md:self-start"
        onError={(e) => {
          const img = e.target as HTMLImageElement;
          if (img.src !== 'https://fakeimg.pl/600x400/ffffff/fffcfc') {
            img.src = 'https://fakeimg.pl/600x400/ffffff/fffcfc';
          }
        }}
      />

      <div className="flex flex-col flex-1">
        <div className="mb-2 flex flex-col md:flex-row items-start md:items-center gap-1 md:gap-2">
          <h3 className="text-[16px] font-['SFProTextBold'] text-[#222222] md:text-left">
            {name}
          </h3>
          <p className="text-[#515151] text-sm md:text-base md:text-left">
            {role}({province_name})
          </p>
        </div>

        <p className="text-[#515151] text-sm mb-3.5 md:text-left">
          {election_summary}
        </p>

        <div>
          <h4 className="text-[#515151] font-['SFProTextMedium'] mb-2 border-t-[0.5px] border-[#B4B4B4] pt-2">
            Recent Activities:
          </h4>
          <div className="space-y-2">
            {/* {recent_activities.map((activity, index) => (
              <div
                key={index}
                className=" items-start md:items-center gap-1 md:gap-2"
              >
                <span
                  className={`text-sm font-['SFProTextMedium'] ${getActivityStyle(
                    activity.title,
                  )}`}
                >
                  {activity.title}{' '}
                  <span
                    className={`text-sm font-['SFProTextMedium'] text-[#515151]`}
                  >
                    {activity.text}
                  </span>
                </span>
                <p className="text-sm text-[#515151] text-italic">
                  {activity.subtitle}
                </p>
              </div>
            ))} */}
            {recent_activities.map((activity, index) => (
              <div key={index} className={`py-2`}>
                {activity.isTitle ? (
                  <p className="text-[#515151] font-['SFProTextMedium'] mb-1 border-b border-t border-[#EDEDED] pb-2 pt-2">
                    {activity.title}
                  </p>
                ) : (
                  <div className="flex flex-col gap-2">
                    <div className=" max-sm:flex-col gap-2">
                      <span
                        className={`text-sm font-['SFProTextMedium'] whitespace-nowrap ${getActivityStyle(
                          activity.title,
                        )}`}
                      >
                        {activity.title}
                      </span>
                      <span className="text-sm text-[#515151]">
                        {' '}
                        {parse(activity.text, options)}
                      </span>
                    </div>
                    {activity.subtitle && (
                      <div className="pl-6 ml-2 border-l-2 border-[#EDEDED]">
                        <p className="text-sm text-[#515151]">
                          {activity.subtitle}
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        <Link
          to={`/mps/${id}`}
          className="text-[#628ECB] mt-4 text-left hover:text-[#4A6B99] transition-colors"
        >
          See More
        </Link>
      </div>
    </div>
  );
};

export default MPCard;
