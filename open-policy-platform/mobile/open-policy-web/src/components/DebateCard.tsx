import React, { useState, useRef, useEffect } from 'react';
import parse, { domToReact } from 'html-react-parser';
import { Link, useLocation } from 'react-router-dom';

export interface Debate {
  name: string;
  riding: string;
  party: string;
  statement: string;
  topic: string;
  sub_topics: string;
  datetime: string;
  profile_url: string;
  image: string;
}

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

// Global scroll and count state
let hasScrolled = false;
let lastPath = '';
const politicianCountMap: Record<string, number> = {};

const DebateCard: React.FC<any> = ({
  debate,
  index,
  politician = null,
  speech_number = null,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const cardRef = useRef<HTMLDivElement>(null);
  const location = useLocation();

  useEffect(() => {
    // Reset state if path changed
    if (lastPath !== location.pathname) {
      hasScrolled = false;
      lastPath = location.pathname;
      Object.keys(politicianCountMap).forEach((key) => {
        politicianCountMap[key] = 0;
      });
    }

    if (debate.name === politician && speech_number != null) {
      // Increment appearance count
      politicianCountMap[politician] =
        (politicianCountMap[politician] || 0) + 1;

      const expectedCount = parseInt(speech_number);

      if (
        !hasScrolled &&
        politicianCountMap[politician] === expectedCount &&
        cardRef.current
      ) {
        const top =
          cardRef.current.getBoundingClientRect().top + window.scrollY;
        window.scrollTo({
          top: top - 400,
          behavior: 'smooth',
        });
        hasScrolled = true;
      }
    }
  }, [debate.name, politician, speech_number, location.pathname]);

  return (
    <div
      ref={cardRef}
      key={index}
      className={`flex flex-col md:flex-row gap-4 md:gap-6 p-4 md:p-6 rounded-[24px] min-h-[200px] w-full justify-start md:justify-start items-start shadow-md`}
      style={{
        backgroundColor: debate.name === politician ? '#fff2b5' : 'transparent',
      }}
    >
      <div className="flex flex-col items-start md:items-end min-w-0 md:min-w-[200px] w-full md:w-auto">
        <h3 className="font-['SFProTextMedium'] text-[#222222] text-sm md:text-sm text-right max-w-[200px]">
          {debate.topic}
        </h3>
        <div className="text-sm text-[#515151]"></div>
        <p className="text-sm text-[#515151]">{debate.sub_topics}</p>
        <p className="text-sm text-[#515151] text-right">{debate.datetime}</p>
        <p
          className="text-sm"
          style={{
            color:
              debate.party == 'Bloc'
                ? '#8AC0DD'
                : debate.party == 'Liberal'
                ? '#FF9999'
                : debate.party == 'Green'
                ? '#A9FA98'
                : debate.party == 'Conservative'
                ? '#AECBF4'
                : debate.party == 'NDP'
                ? '#F7B86D'
                : '#DD3434',
          }}
        >
          {debate.party}
        </p>
      </div>
      <div className="flex flex-col md:flex-row gap-4 w-full md:w-auto">
        <img
          src={
            debate.image ||
            'https://media.istockphoto.com/id/2041572395/vector/blank-avatar-photo-placeholder-icon-vector-illustration.webp?b=1&s=612x612&w=0&k=20&c=88LuT9lqQ6gHAvy7aQfxnRs_iK6KpnE-8QHDw3YyAUU='
          }
          className="w-[80px] h-[80px] md:w-[120px] md:h-[120px] object-contain"
          onError={(e) => {
            const img = e.target as HTMLImageElement;
            if (
              img.src !==
              'https://media.istockphoto.com/id/2041572395/vector/blank-avatar-photo-placeholder-icon-vector-illustration.webp?b=1&s=612x612&w=0&k=20&c=88LuT9lqQ6gHAvy7aQfxnRs_iK6KpnE-8QHDw3YyAUU='
            ) {
              img.src =
                'https://media.istockphoto.com/id/2041572395/vector/blank-avatar-photo-placeholder-icon-vector-illustration.webp?b=1&s=612x612&w=0&k=20&c=88LuT9lqQ6gHAvy7aQfxnRs_iK6KpnE-8QHDw3YyAUU=';
            }
          }}
        />
        <div className="flex flex-col flex-grow">
          <div className="mb-2 flex items-center gap-2">
            <h4 className="text-base md:text-lg font-['SFProTextMedium']">
              <Link to={debate.profile_url}>{debate.name}</Link>
            </h4>
            <p className="text-sm text-[#515151]">{debate.riding}</p>
          </div>
          <p
            className={`text-[#515151] text-sm md:text-base ${
              !isExpanded ? 'line-clamp-4' : ''
            } max-w-full md:max-w-[852px] transition-all duration-300 ease-in-out`}
          >
            {parse(debate.statement, options)}
          </p>
          <button
            className="text-[#628ECB] mt-2 text-left hover:text-[#4A6B99] transition-colors cursor-pointer"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            {debate.statement.split(' ').length > 50 &&
              (isExpanded ? 'Read Less' : 'Read More')}
          </button>
        </div>
      </div>
    </div>
  );
};

export default DebateCard;
