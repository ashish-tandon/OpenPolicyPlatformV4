import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
} from 'react-native';
import React, { useRef, useState } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useAlert } from '../context/AlertProvider';

const VerificationCode = () => {
  const [code, setCode] = useState(['', '', '', '']);
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(false);
  const inputs = useRef([]);
  const { showSuccess } = useAlert();

  const handleChange = (text, index) => {
    setLoading(false);
    setError(false);

    const newCode = [...code];
    newCode[index] = text;
    setCode(newCode);

    if (text) {
      if (index < 3) {
        inputs.current[index + 1]?.focus();
      } else {
        handleSubmit(newCode);
      }
    }
  };

  const handleSubmit = (newCode) => {
    setLoading(true);
    setError(false);

    if (newCode.join('') === '1234') {
      setLoading(false);
      showSuccess('Code Verified!');
      router.push('/password-setup');
      return;
    } else {
      setError(true);
      setLoading(false);
    }
  };

  return (
    <SafeAreaView className="bg-white h-full">
      <ScrollView contentContainerStyle={{ height: '100%' }}>
        <View className="flex-1 px-6 pt-8">
          {/* Back Icon and Progress Bar */}
          <View className="flex-row items-center mb-10">
            <TouchableOpacity className="mr-9" onPress={() => router.back()}>
              <Ionicons name="chevron-back" size={24} color="black" />
            </TouchableOpacity>
            <View className="h-1 w-[202px] bg-gray-200 ml-9">
              <View className="h-1 bg-black w-3/5" />
            </View>
          </View>

          {/* Header */}
          <Text className="text-blue-300 text-center font-semibold mb-5 mt-8">
            OpenPolicy
          </Text>
          <Text className="text-2xl font-bold text-black text-center mb-10">
            Verify your phone
          </Text>
          {/* Input Fields */}
          <View className="flex-row justify-center space-x-4 mb-4">
            {code.map((digit, index) => (
              <TextInput
                key={index}
                value={digit}
                maxLength={1}
                keyboardType="number-pad"
                onChangeText={(text) => handleChange(text, index)}
                ref={(input) => (inputs.current[index] = input)}
                className={`h-[64px] w-[64px] mr-2 text-lg border ${
                  error ? 'border-red-500' : 'border-gray-300'
                } text-center rounded-2xl`}
              />
            ))}
          </View>

          {/* Error Message */}
          {error && (
            <Text className="text-red-500 text-center mb-4">Invalid code</Text>
          )}

          {/* Resend Code */}
          <TouchableOpacity>
            <Text className="text-blue-500 text-center font-medium">
              Resend code
            </Text>
          </TouchableOpacity>

          {/* Loading Indicator */}
          {loading && (
            <View className="items-center mt-6">
              <ActivityIndicator size="large" color="gray" />
            </View>
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

export default VerificationCode;
