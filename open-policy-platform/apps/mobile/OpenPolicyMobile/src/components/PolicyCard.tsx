import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Image,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { format } from 'date-fns';

interface Policy {
  id: string;
  title: string;
  summary: string;
  status: 'draft' | 'active' | 'passed' | 'rejected';
  category: string;
  sponsor: string;
  date: string;
  votes: {
    for: number;
    against: number;
  };
  image?: string;
}

interface PolicyCardProps {
  policy: Policy;
  onPress: (policy: Policy) => void;
}

const PolicyCard: React.FC<PolicyCardProps> = ({ policy, onPress }) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return '#4CAF50';
      case 'passed':
        return '#2196F3';
      case 'rejected':
        return '#F44336';
      default:
        return '#757575';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return 'pending';
      case 'passed':
        return 'check-circle';
      case 'rejected':
        return 'cancel';
      default:
        return 'schedule';
    }
  };

  return (
    <TouchableOpacity
      style={styles.container}
      onPress={() => onPress(policy)}
      activeOpacity={0.8}
    >
      <View style={styles.content}>
        <View style={styles.header}>
          <View style={styles.statusContainer}>
            <Icon
              name={getStatusIcon(policy.status)}
              size={16}
              color={getStatusColor(policy.status)}
            />
            <Text style={[styles.status, { color: getStatusColor(policy.status) }]}>
              {policy.status.toUpperCase()}
            </Text>
          </View>
          <Text style={styles.category}>{policy.category}</Text>
        </View>

        <Text style={styles.title} numberOfLines={2}>
          {policy.title}
        </Text>

        <Text style={styles.summary} numberOfLines={3}>
          {policy.summary}
        </Text>

        <View style={styles.footer}>
          <View style={styles.sponsor}>
            <Icon name="person" size={14} color="#666" />
            <Text style={styles.sponsorText}>{policy.sponsor}</Text>
          </View>
          <Text style={styles.date}>
            {format(new Date(policy.date), 'MMM d, yyyy')}
          </Text>
        </View>

        {policy.votes && (
          <View style={styles.votesContainer}>
            <View style={styles.voteBar}>
              <View
                style={[
                  styles.voteProgress,
                  {
                    flex: policy.votes.for,
                    backgroundColor: '#4CAF50',
                  },
                ]}
              />
              <View
                style={[
                  styles.voteProgress,
                  {
                    flex: policy.votes.against,
                    backgroundColor: '#F44336',
                  },
                ]}
              />
            </View>
            <View style={styles.voteLabels}>
              <Text style={styles.voteText}>
                For: {policy.votes.for}
              </Text>
              <Text style={styles.voteText}>
                Against: {policy.votes.against}
              </Text>
            </View>
          </View>
        )}
      </View>

      {policy.image && (
        <Image
          source={{ uri: policy.image }}
          style={styles.image}
          resizeMode="cover"
        />
      )}
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#fff',
    borderRadius: 12,
    marginHorizontal: 16,
    marginVertical: 8,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
    overflow: 'hidden',
  },
  content: {
    padding: 16,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  statusContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  status: {
    fontSize: 12,
    fontWeight: '600',
    marginLeft: 4,
  },
  category: {
    fontSize: 12,
    color: '#666',
    backgroundColor: '#f0f0f0',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
    lineHeight: 24,
  },
  summary: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
    marginBottom: 12,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  sponsor: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  sponsorText: {
    fontSize: 12,
    color: '#666',
    marginLeft: 4,
  },
  date: {
    fontSize: 12,
    color: '#999',
  },
  votesContainer: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
  },
  voteBar: {
    height: 4,
    backgroundColor: '#f0f0f0',
    borderRadius: 2,
    flexDirection: 'row',
    overflow: 'hidden',
    marginBottom: 8,
  },
  voteProgress: {
    height: '100%',
  },
  voteLabels: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  voteText: {
    fontSize: 12,
    color: '#666',
  },
  image: {
    height: 150,
    width: '100%',
    backgroundColor: '#f0f0f0',
  },
});

export default PolicyCard;